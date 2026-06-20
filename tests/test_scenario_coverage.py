from qa_testgen.domain.enums import ScenarioType, ValidationStatus
from qa_testgen.domain.models import (
    BDDScenario,
    BDDStep,
    Requirement,
    ScenarioValidationReport,
)
from qa_testgen.domain.models import (
    TestOracle as Oracle,
)
from qa_testgen.services.scenario_coverage import ScenarioCoverageChecker


def _scenario(scenario_type: ScenarioType) -> BDDScenario:
    return BDDScenario(
        id=f"SCN-REQ-001-{scenario_type.value}",
        requirement_id="REQ-001",
        title=scenario_type.value,
        scenario_type=scenario_type,
        steps=[
            BDDStep(keyword="Given", text="input"),
            BDDStep(keyword="When", text="action"),
            BDDStep(keyword="Then", text="result"),
        ],
        oracle=Oracle(
            description="Expected behavior",
            assertion_intent="Compare exact result",
            expected_result="expected",
        ),
        rationale="Covers one scenario type",
    )


def _valid_report() -> ScenarioValidationReport:
    return ScenarioValidationReport(
        status=ValidationStatus.VALID,
        score=1.0,
        issues=[],
        missing_requirements=[],
        duplicated_scenarios=[],
        recommendations=[],
    )


def test_incomplete_type_coverage_cannot_remain_valid() -> None:
    report = ScenarioCoverageChecker().enforce_coverage(
        [Requirement(id="REQ-001", text="A requirement")],
        [_scenario(ScenarioType.POSITIVE)],
        _valid_report(),
    )

    assert report.status is ValidationStatus.NEEDS_REVISION
    assert report.score == 0.2
    assert len(report.issues) == 1
    assert "negative" in report.issues[0].message
    assert "error_handling" in report.recommendations[0]


def test_all_scenario_types_preserve_valid_report() -> None:
    original = _valid_report()
    result = ScenarioCoverageChecker().enforce_coverage(
        [Requirement(id="REQ-001", text="A requirement")],
        [_scenario(scenario_type) for scenario_type in ScenarioType],
        original,
    )

    assert result is original


def test_coverage_check_does_not_downgrade_invalid_report() -> None:
    report = _valid_report().model_copy(update={"status": ValidationStatus.INVALID})

    result = ScenarioCoverageChecker().enforce_coverage(
        [Requirement(id="REQ-001", text="A requirement")],
        [_scenario(ScenarioType.POSITIVE)],
        report,
    )

    assert result.status is ValidationStatus.INVALID
