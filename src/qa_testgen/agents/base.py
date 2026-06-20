import json
import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from qa_testgen.config.settings import AppSettings
from qa_testgen.llm.base import BaseLLMClient

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")
ModelT = TypeVar("ModelT", bound=BaseModel)


class AgentExecutionError(RuntimeError):
    """Ошибка исполнения агента с понятным контекстом этапа."""


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Общая оболочка LLM-агента с логированием и точками расширения."""

    def __init__(
        self, llm_client: BaseLLMClient, settings: AppSettings, agent_name: str
    ) -> None:
        self.llm_client = llm_client
        self.settings = settings
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"qa_testgen.agents.{agent_name}")

    @abstractmethod
    def run(self, input_data: InputT) -> OutputT:
        """Выполняет единственную ответственность конкретного агента."""
        raise NotImplementedError

    @abstractmethod
    def _build_system_prompt(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _build_user_prompt(self, input_data: InputT) -> str:
        raise NotImplementedError

    def _log_start(self, **context: object) -> None:
        self.logger.info("Agent %s started: %s", self.agent_name, context)
        self._trace("start", context)

    def _log_finish(self, **context: object) -> None:
        self.logger.info("Agent %s finished: %s", self.agent_name, context)
        self._trace("finish", context)

    def _trace(self, event: str, context: dict[str, object]) -> None:
        """Точка расширения для tracing без изменения дочерних агентов."""
        self.logger.debug("Trace event=%s context=%s", event, context)

    def _invoke_model(
        self,
        system_prompt: str,
        user_prompt: str,
        model_type: type[ModelT],
    ) -> ModelT:
        """Запрашивает JSON, валидирует схему и исправляет только её нарушения."""
        schema = model_type.model_json_schema()
        schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
        prompt_with_schema = (
            f"{user_prompt}\n\n"
            "ОБЯЗАТЕЛЬНАЯ JSON SCHEMA ОТВЕТА:\n"
            f"{schema_json}\n\n"
            "Все обязательные поля должны присутствовать под точными именами и "
            "иметь типы, указанные в schema."
        )
        raw = self.llm_client.invoke_json(system_prompt, prompt_with_schema)

        for repair_attempt in range(
            self.settings.max_llm_schema_repair_attempts + 1
        ):
            try:
                return model_type.model_validate(raw)
            except ValidationError as exc:
                if repair_attempt >= self.settings.max_llm_schema_repair_attempts:
                    errors = self._compact_validation_errors(exc)
                    raise AgentExecutionError(
                        f"Agent {self.agent_name} returned invalid "
                        f"{model_type.__name__} after schema repair: {errors}"
                    ) from exc
                self.logger.warning(
                    "Invalid %s schema; requesting repair attempt %d/%d",
                    model_type.__name__,
                    repair_attempt + 1,
                    self.settings.max_llm_schema_repair_attempts,
                )
                raw = self.llm_client.invoke_json(
                    self._schema_repair_system_prompt(),
                    self._schema_repair_user_prompt(raw, schema_json, exc),
                )

        raise AssertionError("Schema validation loop finished unexpectedly")

    @staticmethod
    def _schema_repair_system_prompt() -> str:
        return (
            "Ты исправляешь структуру JSON-ответа. Не добавляй markdown. "
            "Не меняй смысл данных и не создавай новые бизнес-сценарии. "
            "Переименуй и преобразуй поля так, чтобы результат строго соответствовал "
            "переданной JSON Schema. Верни только исправленный JSON-объект."
        )

    @classmethod
    def _schema_repair_user_prompt(
        cls,
        raw: dict[str, object],
        schema_json: str,
        error: ValidationError,
    ) -> str:
        return (
            "JSON SCHEMA:\n"
            f"{schema_json}\n\n"
            "ОШИБКИ ВАЛИДАЦИИ:\n"
            f"{cls._compact_validation_errors(error)}\n\n"
            "ИСХОДНЫЙ JSON ДЛЯ ИСПРАВЛЕНИЯ:\n"
            f"{json.dumps(raw, ensure_ascii=False)}"
        )

    @staticmethod
    def _compact_validation_errors(error: ValidationError) -> str:
        errors = error.errors(include_url=False, include_input=False)
        compact = [
            {"location": ".".join(map(str, item["loc"])), "message": item["msg"]}
            for item in errors[:40]
        ]
        payload = {"total_errors": error.error_count(), "first_errors": compact}
        return json.dumps(payload, ensure_ascii=False)
