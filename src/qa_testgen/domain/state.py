from typing import TypedDict

from qa_testgen.domain.enums import PipelineType
from qa_testgen.domain.models import (
    BDDScenario,
    PytestGenerationResult,
    Requirement,
    ScenarioGenerationResult,
    ScenarioValidationReport,
    SourceCodeInput,
    SyntaxValidationResult,
)


class GraphState(TypedDict):
    pipeline_type: PipelineType
    source_code: SourceCodeInput
    requirements: list[Requirement]
    scenarios: list[BDDScenario]
    scenario_generation_notes: str
    scenario_generation_history: list[ScenarioGenerationResult]
    scenario_validation_report: ScenarioValidationReport | None
    scenario_validation_history: list[ScenarioValidationReport]
    pytest_generation_result: PytestGenerationResult | None
    syntax_validation_result: SyntaxValidationResult | None
    scenario_validation_attempt: int
    test_generation_attempt: int
    errors: list[str]
    artifacts: dict[str, str]
