from abc import ABC, abstractmethod
from typing import Any


class LLMResponseParseError(ValueError):
    """Raised when an LLM response cannot be decoded as a JSON object."""


class BaseLLMClient(ABC):
    @abstractmethod
    def invoke_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError
