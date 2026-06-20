from pathlib import Path
from typing import Any, cast

from pydantic import SecretStr

from qa_testgen.agents.pytest_generator import PytestGeneratorAgent
from qa_testgen.agents.scenario_generator import ScenarioGeneratorAgent
from qa_testgen.agents.scenario_validator import ScenarioValidatorAgent
from qa_testgen.agents.syntax_validator import SyntaxValidatorAgent
from qa_testgen.config.settings import AppSettings
from qa_testgen.domain.enums import PipelineType, ScenarioType
from qa_testgen.domain.state import GraphState
from qa_testgen.graph.builder import TestGenerationGraphBuilder as GraphBuilder
from qa_testgen.llm.base import BaseLLMClient
from qa_testgen.services.artifact_store import ArtifactStore
from qa_testgen.services.syntax_checker import SyntaxChecker
from tests.factories import make_graph_state


class WorkflowFakeLLMClient(BaseLLMClient):
    def invoke_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if "генерации тестовых BDD" in system_prompt:
            return {
                "scenarios": [self._scenario(item) for item in ScenarioType],
                "generation_notes": "All required types generated.",
            }
        if "критик" in system_prompt:
            return {
                "status": "valid",
                "score": 1.0,
                "issues": [],
                "missing_requirements": [],
                "duplicated_scenarios": [],
                "recommendations": [],
            }
        return {
            "requirement_id": "REQ-001",
            "scenario_ids": [f"SCN-{item.value}" for item in ScenarioType],
            "test_code": "# REQ-001\ndef test_value():\n    assert 1 == 1\n",
            "imports": [],
            "notes": "Generated from all scenarios.",
        }

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

    @staticmethod
    def _scenario(scenario_type: ScenarioType) -> dict[str, Any]:
        return {
            "id": f"SCN-{scenario_type.value}",
            "requirement_id": "REQ-001",
            "title": scenario_type.value,
            "scenario_type": scenario_type.value,
            "steps": [
                {"keyword": "Given", "text": "input"},
                {"keyword": "When", "text": "action"},
                {"keyword": "Then", "text": "result"},
            ],
            "oracle": {
                "description": "Expected result",
                "assertion_intent": "Compare exact result",
                "expected_result": "1",
            },
            "covered_conditions": [scenario_type.value],
            "test_data": {},
            "rationale": "Required coverage type",
        }


def test_complete_proposed_graph_records_histories_and_artifacts(
    tmp_path: Path,
) -> None:
    settings = AppSettings(
        llm_provider="openai",
        llm_model="fake",
        llm_temperature=0,
        llm_max_tokens=100,
        openai_api_key=SecretStr("fake"),
        max_scenario_validation_attempts=2,
        max_test_generation_attempts=2,
        artifacts_dir=tmp_path,
        log_level="INFO",
    )
    client = WorkflowFakeLLMClient()
    graph = GraphBuilder(
        ScenarioGeneratorAgent(client, settings),
        ScenarioValidatorAgent(client, settings),
        PytestGeneratorAgent(client, settings),
        SyntaxValidatorAgent(SyntaxChecker()),
        settings,
        ArtifactStore(tmp_path, {"pipeline_type": "proposed"}),
    ).build()
    initial_state = make_graph_state(PipelineType.PROPOSED)
    initial_state["pytest_generation_result"] = None
    initial_state["syntax_validation_result"] = None
    initial_state["test_generation_attempt"] = 0

    result = cast(GraphState, graph.invoke(initial_state))

    assert len(result["scenarios"]) == len(ScenarioType)
    assert len(result["scenario_generation_history"]) == 1
    assert len(result["scenario_validation_history"]) == 1
    assert result["syntax_validation_result"] is not None
    assert result["syntax_validation_result"].is_valid is True
    assert Path(result["artifacts"]["pipeline_result"]).exists()
