from pathlib import Path
from typing import cast

from pydantic import SecretStr

from qa_testgen.agents.scenario_generator import ScenarioGeneratorAgent
from qa_testgen.config.settings import AppSettings
from qa_testgen.domain.enums import ScenarioType, ValidationStatus
from qa_testgen.domain.models import (
    BDDScenario,
    BDDStep,
    ScenarioValidationReport,
    SyntaxValidationResult,
)
from qa_testgen.domain.models import (
    TestOracle as Oracle,
)
from qa_testgen.graph.nodes import (
    SCENARIO_EXHAUSTION_ERROR,
    SCENARIO_REVISION_FALLBACK_ERROR,
    SYNTAX_EXHAUSTION_ERROR,
    generate_scenarios_node,
    record_scenario_exhaustion_node,
    record_syntax_exhaustion_node,
)
from qa_testgen.graph.routers import (
    route_after_scenario_validation,
    route_after_syntax_validation,
)
from qa_testgen.llm.base import LLMResponseParseError
from tests.factories import make_graph_state


class FailingScenarioGenerator:
    def run(self, input_data: object) -> object:
        raise LLMResponseParseError("empty response")


def _settings(tmp_path: Path) -> AppSettings:
    return AppSettings(
        llm_provider="openai",
        llm_model="fake",
        llm_temperature=0,
        llm_max_tokens=100,
        openai_api_key=SecretStr("fake"),
        max_scenario_validation_attempts=1,
        max_test_generation_attempts=1,
        artifacts_dir=tmp_path,
        log_level="INFO",
    )


def test_scenario_router_is_pure_and_routes_to_error_node(tmp_path: Path) -> None:
    state = make_graph_state()
    state["scenario_validation_attempt"] = 1
    state["scenario_validation_report"] = ScenarioValidationReport(
        status=ValidationStatus.NEEDS_REVISION,
        score=0.5,
        issues=[],
        missing_requirements=[],
        duplicated_scenarios=[],
        recommendations=[],
    )

    route = route_after_scenario_validation(state, settings=_settings(tmp_path))

    assert route == "record_scenario_exhaustion"
    assert state["errors"] == []
    assert record_scenario_exhaustion_node(state) == {
        "errors": [SCENARIO_EXHAUSTION_ERROR]
    }


def test_syntax_router_is_pure_and_routes_to_error_node(tmp_path: Path) -> None:
    state = make_graph_state()
    state["syntax_validation_result"] = SyntaxValidationResult(is_valid=False)

    route = route_after_syntax_validation(state, settings=_settings(tmp_path))

    assert route == "record_syntax_exhaustion"
    assert state["errors"] == []
    assert record_syntax_exhaustion_node(state) == {
        "errors": [SYNTAX_EXHAUSTION_ERROR]
    }


def test_failed_revision_keeps_previous_scenarios() -> None:
    state = make_graph_state()
    scenario = BDDScenario(
        id="SCN-001",
        requirement_id="REQ-001",
        title="Previous scenario",
        scenario_type=ScenarioType.POSITIVE,
        steps=[
            BDDStep(keyword="Given", text="input"),
            BDDStep(keyword="When", text="action"),
            BDDStep(keyword="Then", text="result"),
        ],
        oracle=Oracle(
            description="Expected result",
            assertion_intent="Compare result",
            expected_result="value",
        ),
        rationale="Previous successful generation",
    )
    state["scenarios"] = [scenario]

    update = generate_scenarios_node(
        state,
        agent=cast(ScenarioGeneratorAgent, FailingScenarioGenerator()),
    )

    assert "scenarios" not in update
    assert SCENARIO_REVISION_FALLBACK_ERROR in str(update["errors"])
    assert "empty response" in str(update["scenario_generation_notes"])
