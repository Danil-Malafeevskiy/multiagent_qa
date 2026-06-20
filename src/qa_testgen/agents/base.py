import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from qa_testgen.config.settings import AppSettings
from qa_testgen.llm.base import BaseLLMClient

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


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
