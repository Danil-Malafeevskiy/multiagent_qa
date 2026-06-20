from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator

from qa_testgen.domain.enums import PipelineType, ScenarioType, ValidationStatus


class SourceCodeInput(BaseModel):
    project_name: str
    files: dict[str, str]


class Requirement(BaseModel):
    id: str
    text: str
    priority: str | None = None
    tags: list[str] = Field(default_factory=list)


class TestOracle(BaseModel):
    description: str
    assertion_intent: str
    expected_result: str


class BDDStep(BaseModel):
    keyword: Literal["Given", "When", "Then", "And"]
    text: str


class BDDScenario(BaseModel):
    id: str
    requirement_id: str
    title: str
    scenario_type: ScenarioType
    steps: list[BDDStep]
    oracle: TestOracle
    covered_conditions: list[str] = Field(default_factory=list)
    test_data: dict[str, Any] = Field(default_factory=dict)
    rationale: str

    @model_validator(mode="after")
    def validate_bdd_step_sequence(self) -> Self:
        first_positions: dict[str, int] = {}
        for index, step in enumerate(self.steps):
            first_positions.setdefault(step.keyword, index)

        required = ("Given", "When", "Then")
        missing = [keyword for keyword in required if keyword not in first_positions]
        if missing:
            raise ValueError(f"BDD scenario is missing steps: {', '.join(missing)}")
        if not (
            first_positions["Given"]
            < first_positions["When"]
            < first_positions["Then"]
        ):
            raise ValueError("BDD steps must follow Given -> When -> Then order")
        return self


class ScenarioGenerationResult(BaseModel):
    scenarios: list[BDDScenario]
    generation_notes: str


class ScenarioValidationIssue(BaseModel):
    severity: Literal["low", "medium", "high"]
    scenario_id: str | None = None
    requirement_id: str | None = None
    message: str
    recommendation: str


class ScenarioValidationReport(BaseModel):
    status: ValidationStatus
    score: float = Field(ge=0, le=1)
    issues: list[ScenarioValidationIssue] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    duplicated_scenarios: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class PytestGenerationResult(BaseModel):
    requirement_id: str
    scenario_ids: list[str]
    test_code: str
    imports: list[str]
    notes: str


class SyntaxValidationResult(BaseModel):
    is_valid: bool
    error_message: str | None = None
    line_number: int | None = None
    details: str | None = None


class PipelineResult(BaseModel):
    pipeline_type: PipelineType
    requirements: list[Requirement]
    scenarios: list[BDDScenario]
    scenario_generation_notes: str = ""
    validation_report: ScenarioValidationReport | None = None
    pytest_result: PytestGenerationResult | None = None
    syntax_result: SyntaxValidationResult | None = None
    artifacts_path: str | None = None
