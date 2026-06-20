from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage
from pydantic import SecretStr

from qa_testgen.config.settings import AppSettings
from qa_testgen.llm import openai_client as openai_client_module
from qa_testgen.llm.openai_client import OpenAILLMClient


class FakeChatOpenAI:
    def __init__(self, responses: list[AIMessage]) -> None:
        self.responses = iter(responses)
        self.calls: list[list[Any]] = []

    def invoke(self, messages: list[Any]) -> AIMessage:
        self.calls.append(messages)
        return next(self.responses)


def _settings(tmp_path: Path) -> AppSettings:
    return AppSettings(
        llm_provider="openai",
        llm_model="fake",
        llm_temperature=0,
        llm_max_tokens=100,
        llm_request_timeout_seconds=42,
        llm_http_max_retries=3,
        openai_api_key=SecretStr("fake"),
        max_scenario_validation_attempts=1,
        max_test_generation_attempts=1,
        max_llm_response_parse_retries=1,
        artifacts_dir=tmp_path,
        log_level="INFO",
    )


def test_empty_response_is_retried_and_fenced_json_is_parsed(
    tmp_path: Path, monkeypatch: Any
) -> None:
    fake_chat = FakeChatOpenAI(
        [
            AIMessage(content="", response_metadata={"finish_reason": "stop"}),
            AIMessage(content='Ответ:\n```json\n{"status": "ok"}\n```'),
        ]
    )
    captured_kwargs: dict[str, Any] = {}

    def fake_constructor(**kwargs: Any) -> FakeChatOpenAI:
        captured_kwargs.update(kwargs)
        return fake_chat

    monkeypatch.setattr(openai_client_module, "ChatOpenAI", fake_constructor)
    client = OpenAILLMClient(_settings(tmp_path))

    result = client.invoke_json("system", "user")

    assert result == {"status": "ok"}
    assert len(fake_chat.calls) == 2
    assert "ПРЕДЫДУЩИЙ ОТВЕТ" in fake_chat.calls[1][1].content
    assert captured_kwargs["timeout"] == 42
    assert captured_kwargs["max_retries"] == 3


def test_json_object_can_be_extracted_from_plain_prose() -> None:
    result = OpenAILLMClient._decode_json_object(
        'Сформирован результат: {"status": "ok"} Готово.'
    )

    assert result == {"status": "ok"}

