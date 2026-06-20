from qa_testgen.agents.base import AgentExecutionError
from qa_testgen.agents.pytest_generator import (
    PytestGeneratorAgent,
    PytestGeneratorInput,
    PytestRepairInput,
)
from qa_testgen.agents.scenario_generator import (
    ScenarioGeneratorAgent,
    ScenarioGeneratorInput,
)
from qa_testgen.agents.scenario_validator import (
    ScenarioValidatorAgent,
    ScenarioValidatorInput,
)
from qa_testgen.agents.syntax_validator import SyntaxValidatorAgent
from qa_testgen.domain.state import GraphState
from qa_testgen.llm.base import LLMResponseParseError
from qa_testgen.services.artifact_store import ArtifactStore

SCENARIO_EXHAUSTION_ERROR = (
    "Scenario validation attempts exhausted; generating pytest with warnings."
)
SYNTAX_EXHAUSTION_ERROR = (
    "Test generation attempts exhausted; saving syntactically invalid output."
)
SCENARIO_REVISION_FALLBACK_ERROR = (
    "Scenario revision failed; keeping the previous scenario set."
)


def generate_scenarios_node(
    state: GraphState, *, agent: ScenarioGeneratorAgent
) -> dict[str, object]:
    try:
        result = agent.run(
            ScenarioGeneratorInput(
                source_code=state["source_code"],
                requirements=state["requirements"],
                previous_scenarios=state["scenarios"],
                validation_report=state["scenario_validation_report"],
            )
        )
    except (AgentExecutionError, LLMResponseParseError) as exc:
        if not state["scenarios"]:
            raise
        error = f"{SCENARIO_REVISION_FALLBACK_ERROR} Cause: {exc}"
        return {
            "scenario_generation_notes": error,
            "errors": [*state["errors"], error],
        }
    return {
        "scenarios": result.scenarios,
        "scenario_generation_notes": result.generation_notes,
        "scenario_generation_history": [
            *state["scenario_generation_history"],
            result,
        ],
    }


def validate_scenarios_node(
    state: GraphState, *, agent: ScenarioValidatorAgent
) -> dict[str, object]:
    report = agent.run(
        ScenarioValidatorInput(
            source_code=state["source_code"],
            requirements=state["requirements"],
            scenarios=state["scenarios"],
            previous_validation_report=state["scenario_validation_report"],
        )
    )
    return {
        "scenario_validation_report": report,
        "scenario_validation_history": [
            *state["scenario_validation_history"],
            report,
        ],
        "scenario_validation_attempt": state["scenario_validation_attempt"] + 1,
    }


def generate_pytest_node(
    state: GraphState, *, agent: PytestGeneratorAgent
) -> dict[str, object]:
    result = agent.run(
        PytestGeneratorInput(
            source_code=state["source_code"],
            scenarios=state["scenarios"],
            validation_report=state["scenario_validation_report"],
        )
    )
    return {
        "pytest_generation_result": result,
        "test_generation_attempt": state["test_generation_attempt"] + 1,
    }


def validate_syntax_node(
    state: GraphState, *, agent: SyntaxValidatorAgent
) -> dict[str, object]:
    pytest_result = state["pytest_generation_result"]
    if pytest_result is None:
        raise ValueError("Pytest generation result is missing")
    return {"syntax_validation_result": agent.run(pytest_result.test_code)}


def repair_pytest_node(
    state: GraphState, *, agent: PytestGeneratorAgent
) -> dict[str, object]:
    pytest_result = state["pytest_generation_result"]
    syntax_result = state["syntax_validation_result"]
    if pytest_result is None or syntax_result is None:
        raise ValueError("Repair requires pytest and syntax validation results")
    result = agent.repair(
        PytestRepairInput(
            source_code=state["source_code"],
            scenarios=state["scenarios"],
            previous_test_code=pytest_result.test_code,
            syntax_error=syntax_result,
        )
    )
    return {
        "pytest_generation_result": result,
        "test_generation_attempt": state["test_generation_attempt"] + 1,
    }


def record_scenario_exhaustion_node(state: GraphState) -> dict[str, object]:
    return {"errors": [*state["errors"], SCENARIO_EXHAUSTION_ERROR]}


def record_syntax_exhaustion_node(state: GraphState) -> dict[str, object]:
    return {"errors": [*state["errors"], SYNTAX_EXHAUSTION_ERROR]}


def save_artifacts_node(
    state: GraphState, *, artifact_store: ArtifactStore
) -> dict[str, object]:
    return {"artifacts": artifact_store.save_pipeline_artifacts(state)}
