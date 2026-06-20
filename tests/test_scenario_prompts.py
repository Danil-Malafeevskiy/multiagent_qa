import json

from qa_testgen.domain.enums import ScenarioType, ValidationStatus
from qa_testgen.domain.models import (
    BDDScenario,
    BDDStep,
    Requirement,
    ScenarioValidationIssue,
    ScenarioValidationReport,
    SourceCodeInput,
)
from qa_testgen.domain.models import (
    TestOracle as Oracle,
)
from qa_testgen.prompts.scenario_prompts import (
    build_scenario_generation_user_prompt,
)
from qa_testgen.prompts.validation_prompts import (
    build_scenario_validation_user_prompt,
)


def _previous_scenario() -> BDDScenario:
    return BDDScenario(
        id="SCN-001",
        requirement_id="REQ-001",
        title="Existing scenario",
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
        rationale="Existing coverage",
    )


def _validation_report() -> ScenarioValidationReport:
    return ScenarioValidationReport(
        status=ValidationStatus.NEEDS_REVISION,
        score=0.5,
        issues=[
            ScenarioValidationIssue(
                severity="high",
                scenario_id="SCN-001",
                requirement_id="REQ-001",
                message="Weak oracle",
                recommendation="Use an exact expected value",
            )
        ],
        missing_requirements=[],
        duplicated_scenarios=[],
        recommendations=["Add a boundary scenario"],
    )


def test_revision_prompt_contains_scenarios_and_every_recommendation() -> None:
    prompt = build_scenario_generation_user_prompt(
        SourceCodeInput(project_name="sample", files={"app.py": "pass"}),
        [Requirement(id="REQ-001", text="A requirement")],
        [_previous_scenario()],
        _validation_report(),
    )
    payload = json.loads(prompt.removeprefix("Входные данные:\n"))

    assert payload["previous_scenarios"][0]["id"] == "SCN-001"
    assert payload["mandatory_recommendations_to_address"] == [
        "Add a boundary scenario",
        "Use an exact expected value",
    ]
    assert len(payload["coverage_policy"]["required_types_per_requirement"]) == 5


def test_validator_prompt_receives_previous_report() -> None:
    prompt = build_scenario_validation_user_prompt(
        SourceCodeInput(project_name="sample", files={"app.py": "pass"}),
        [Requirement(id="REQ-001", text="A requirement")],
        [_previous_scenario()],
        _validation_report(),
    )
    payload = json.loads(prompt.removeprefix("Проверь следующие данные:\n"))

    assert payload["previous_validation_report_to_verify"]["score"] == 0.5
    assert payload["required_types_per_requirement"] == [
        scenario_type.value for scenario_type in ScenarioType
    ]

