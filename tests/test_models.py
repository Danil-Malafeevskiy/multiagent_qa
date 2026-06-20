import pytest
from pydantic import ValidationError

from qa_testgen.domain.enums import ScenarioType, ValidationStatus
from qa_testgen.domain.models import (
    BDDScenario,
    BDDStep,
    ScenarioValidationReport,
)
from qa_testgen.domain.models import (
    TestOracle as Oracle,
)


def test_bdd_scenario_is_created_from_typed_data() -> None:
    scenario = BDDScenario(
        id="SCN-REQ-001-001",
        requirement_id="REQ-001",
        title="Add one item",
        scenario_type=ScenarioType.POSITIVE,
        steps=[
            BDDStep(keyword="Given", text="an empty cart"),
            BDDStep(keyword="When", text="an item is added"),
            BDDStep(keyword="Then", text="the total increases"),
        ],
        oracle=Oracle(
            description="Exact total",
            assertion_intent="Compare the cart total",
            expected_result="20.0",
        ),
        covered_conditions=["quantity is included"],
        test_data={"price": 10.0, "quantity": 2},
        rationale="Directly covers the requirement",
    )

    assert scenario.scenario_type is ScenarioType.POSITIVE
    assert scenario.oracle.expected_result == "20.0"


def test_validation_score_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValidationError):
        ScenarioValidationReport(
            status=ValidationStatus.VALID,
            score=1.5,
            issues=[],
            missing_requirements=[],
            duplicated_scenarios=[],
            recommendations=[],
        )


def test_bdd_scenario_requires_given_when_then_order() -> None:
    with pytest.raises(ValidationError, match="Given -> When -> Then"):
        BDDScenario(
            id="SCN-001",
            requirement_id="REQ-001",
            title="Wrong order",
            scenario_type=ScenarioType.POSITIVE,
            steps=[
                BDDStep(keyword="When", text="action"),
                BDDStep(keyword="Given", text="input"),
                BDDStep(keyword="Then", text="result"),
            ],
            oracle=Oracle(
                description="Expected result",
                assertion_intent="Compare result",
                expected_result="value",
            ),
            rationale="Invalid test fixture",
        )
