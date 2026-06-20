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
from qa_testgen.services.artifact_store import ArtifactStore


def generate_scenarios_node(
    state: GraphState, *, agent: ScenarioGeneratorAgent
) -> dict[str, object]:
    result = agent.run(
        ScenarioGeneratorInput(
            source_code=state["source_code"],
            requirements=state["requirements"],
            validation_report=state["scenario_validation_report"],
        )
    )
    return {"scenarios": result.scenarios}


def validate_scenarios_node(
    state: GraphState, *, agent: ScenarioValidatorAgent
) -> dict[str, object]:
    report = agent.run(
        ScenarioValidatorInput(
            source_code=state["source_code"],
            requirements=state["requirements"],
            scenarios=state["scenarios"],
        )
    )
    return {
        "scenario_validation_report": report,
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


def save_artifacts_node(
    state: GraphState, *, artifact_store: ArtifactStore
) -> dict[str, object]:
    return {"artifacts": artifact_store.save_pipeline_artifacts(state)}
