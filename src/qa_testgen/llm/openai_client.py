import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from qa_testgen.config.settings import AppSettings
from qa_testgen.llm.base import BaseLLMClient, LLMResponseParseError


class OpenAILLMClient(BaseLLMClient):
    def __init__(self, settings: AppSettings) -> None:
        self._logger = logging.getLogger("qa_testgen.llm.openai")
        self._max_response_parse_retries = settings.max_llm_response_parse_retries
        self._client = ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.llm_request_timeout_seconds,
            max_retries=settings.llm_http_max_retries,
            api_key=settings.openai_api_key,
        )

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        content = self._content_to_text(response.content).strip()
        if not content:
            finish_reason = response.response_metadata.get("finish_reason", "unknown")
            raise LLMResponseParseError(
                f"LLM returned empty content (finish_reason={finish_reason})"
            )
        return content

    def invoke_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        last_error: LLMResponseParseError | None = None
        for attempt in range(self._max_response_parse_retries + 1):
            retry_prompt = self._build_retry_prompt(user_prompt, attempt)
            try:
                raw_response = self.invoke_text(system_prompt, retry_prompt)
                return self._decode_json_object(raw_response)
            except LLMResponseParseError as exc:
                last_error = exc
                if attempt >= self._max_response_parse_retries:
                    break
                self._logger.warning(
                    "LLM JSON response could not be parsed; retrying %d/%d: %s",
                    attempt + 1,
                    self._max_response_parse_retries,
                    exc,
                )

        raise LLMResponseParseError(
            f"LLM did not return a valid JSON object after "
            f"{self._max_response_parse_retries + 1} attempts: {last_error}"
        ) from last_error

    @classmethod
    def _decode_json_object(cls, response: str) -> dict[str, Any]:
        candidate = cls._extract_json(response)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            parsed = cls._extract_embedded_object(candidate)
            if parsed is None:
                preview = candidate[:200].replace("\n", "\\n")
                raise LLMResponseParseError(
                    f"LLM response is not valid JSON: {exc.msg} at line "
                    f"{exc.lineno}; response_preview={preview!r}"
                ) from exc
        if not isinstance(parsed, dict):
            raise LLMResponseParseError("LLM JSON response must be an object")
        return parsed

    @staticmethod
    def _extract_json(response: str) -> str:
        fenced = re.search(
            r"```(?:json)?\s*(.*?)\s*```", response, flags=re.DOTALL | re.I
        )
        return fenced.group(1).strip() if fenced else response.strip()

    @staticmethod
    def _extract_embedded_object(response: str) -> dict[str, Any] | None:
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", response):
            try:
                parsed, _ = decoder.raw_decode(response[match.start() :])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and isinstance(block.get("text"), str):
                    parts.append(block["text"])
            if parts:
                return "\n".join(parts)
        raise LLMResponseParseError("LLM returned non-text message content")

    @staticmethod
    def _build_retry_prompt(user_prompt: str, attempt: int) -> str:
        if attempt == 0:
            return user_prompt
        return (
            f"{user_prompt}\n\n"
            "ПРЕДЫДУЩИЙ ОТВЕТ БЫЛ ПУСТЫМ ИЛИ НЕ ЯВЛЯЛСЯ ВАЛИДНЫМ JSON. "
            "Повтори ответ полностью. Верни только один JSON-объект без markdown, "
            "пояснений и текста до или после JSON."
        )


def create_llm_client(settings: AppSettings) -> BaseLLMClient:
    provider = settings.llm_provider.casefold()
    if provider == "openai":
        return OpenAILLMClient(settings)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
