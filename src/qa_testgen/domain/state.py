from typing import TypedDict

from qa_testgen.domain.models import (
    BDDScenario,
    PytestGenerationResult,
    Requirement,
    ScenarioValidationReport,
    SourceCodeInput,
    SyntaxValidationResult,
)


class GraphState(TypedDict):
    source_code: SourceCodeInput
    requirements: list[Requirement]
    scenarios: list[BDDScenario]
    scenario_validation_report: ScenarioValidationReport | None
    pytest_generation_result: PytestGenerationResult | None
    syntax_validation_result: SyntaxValidationResult | None
    scenario_validation_attempt: int
    test_generation_attempt: int
    errors: list[str]
    artifacts: dict[str, str]
