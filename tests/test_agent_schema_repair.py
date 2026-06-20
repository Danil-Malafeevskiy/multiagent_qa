from pathlib import Path
from typing import Any

from pydantic import SecretStr

from qa_testgen.agents.scenario_generator import (
    ScenarioGeneratorAgent,
    ScenarioGeneratorInput,
)
from qa_testgen.config.settings import AppSettings
from qa_testgen.domain.models import Requirement, SourceCodeInput
from qa_testgen.llm.base import BaseLLMClient


class SchemaRepairFakeLLMClient(BaseLLMClient):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def invoke_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        self.calls.append((system_prompt, user_prompt))
        if len(self.calls) == 1:
            return {
                "scenarios": [
                    {
                        "id": "SCN-001",
                        "requirement_id": "REQ-001",
                        "title": "Incorrect shape",
                        "type": "positive",
                        "given": "a value",
                        "when": "the function is called",
                        "then": "the value is returned",
                        "oracle": {
                            "assertion_intent": "Compare values",
                            "expected_result": "1",
                        },
                        "rationale": "Direct coverage",
                    }
                ],
                "generation_notes": ["Wrong list type"],
            }
        return {
            "scenarios": [
                {
                    "id": "SCN-001",
                    "requirement_id": "REQ-001",
                    "title": "Correct shape",
                    "scenario_type": "positive",
                    "steps": [
                        {"keyword": "Given", "text": "a value"},
                        {"keyword": "When", "text": "the function is called"},
                        {"keyword": "Then", "text": "the value is returned"},
                    ],
                    "oracle": {
                        "description": "The exact value is returned",
                        "assertion_intent": "Compare values",
                        "expected_result": "1",
                    },
                    "covered_conditions": ["normal input"],
                    "test_data": {"value": 1},
                    "rationale": "Direct coverage",
                }
            ],
            "generation_notes": "Schema repaired",
        }

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


def test_scenario_agent_repairs_invalid_llm_schema(tmp_path: Path) -> None:
    settings = AppSettings(
        llm_provider="openai",
        llm_model="fake",
        llm_temperature=0,
        llm_max_tokens=100,
        openai_api_key=SecretStr("fake"),
        max_scenario_validation_attempts=1,
        max_test_generation_attempts=1,
        max_llm_schema_repair_attempts=1,
        artifacts_dir=tmp_path,
        log_level="INFO",
    )
    client = SchemaRepairFakeLLMClient()
    agent = ScenarioGeneratorAgent(client, settings)

    result = agent.run(
        ScenarioGeneratorInput(
            source_code=SourceCodeInput(
                project_name="sample", files={"app.py": "def value(): return 1"}
            ),
            requirements=[Requirement(id="REQ-001", text="Return one")],
        )
    )

    assert len(client.calls) == 2
    assert "JSON SCHEMA" in client.calls[0][1]
    assert "ОШИБКИ ВАЛИДАЦИИ" in client.calls[1][1]
    assert result.scenarios[0].scenario_type.value == "positive"
    assert result.generation_notes == "Schema repaired"

