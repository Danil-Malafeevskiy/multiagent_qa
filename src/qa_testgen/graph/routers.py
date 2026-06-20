from qa_testgen.config.settings import AppSettings
from qa_testgen.domain.enums import ValidationStatus
from qa_testgen.domain.state import GraphState


def route_after_scenario_validation(state: GraphState, *, settings: AppSettings) -> str:
    report = state["scenario_validation_report"]
    if report is None:
        raise ValueError("Scenario validation report is missing")
    if report.status == ValidationStatus.VALID:
        return "generate_pytest"
    if state["scenario_validation_attempt"] < settings.max_scenario_validation_attempts:
        return "generate_scenarios"
    return "record_scenario_exhaustion"


def route_after_syntax_validation(state: GraphState, *, settings: AppSettings) -> str:
    result = state["syntax_validation_result"]
    if result is None:
        raise ValueError("Syntax validation result is missing")
    if result.is_valid:
        return "save_artifacts"
    if state["test_generation_attempt"] < settings.max_test_generation_attempts:
        return "repair_pytest"
    return "record_syntax_exhaustion"
