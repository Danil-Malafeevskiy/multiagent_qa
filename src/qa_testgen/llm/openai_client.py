import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from qa_testgen.config.settings import AppSettings
from qa_testgen.llm.base import BaseLLMClient, LLMResponseParseError


class OpenAILLMClient(BaseLLMClient):
    def __init__(self, settings: AppSettings) -> None:
        self._client = ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key,
        )

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        if not isinstance(response.content, str):
            raise LLMResponseParseError("LLM returned non-text message content")
        return response.content.strip()

    def invoke_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        raw_response = self.invoke_text(system_prompt, user_prompt)
        candidate = self._extract_json(raw_response)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise LLMResponseParseError(
                f"LLM response is not valid JSON: {exc.msg} at line {exc.lineno}"
            ) from exc
        if not isinstance(parsed, dict):
            raise LLMResponseParseError("LLM JSON response must be an object")
        return parsed

    @staticmethod
    def _extract_json(response: str) -> str:
        fenced = re.fullmatch(
            r"\s*```(?:json)?\s*(.*?)\s*```\s*", response, flags=re.DOTALL | re.I
        )
        return fenced.group(1).strip() if fenced else response.strip()


def create_llm_client(settings: AppSettings) -> BaseLLMClient:
    provider = settings.llm_provider.casefold()
    if provider == "openai":
        return OpenAILLMClient(settings)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
