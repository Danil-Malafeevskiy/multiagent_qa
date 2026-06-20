from typing import Any, Literal

from pydantic import BaseModel, Field

from qa_testgen.domain.enums import ScenarioType, ValidationStatus


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
    requirements: list[Requirement]
    scenarios: list[BDDScenario]
    validation_report: ScenarioValidationReport | None = None
    pytest_result: PytestGenerationResult | None = None
    syntax_result: SyntaxValidationResult | None = None
    artifacts_path: str | None = None
