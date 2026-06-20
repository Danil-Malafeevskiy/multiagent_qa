from collections import Counter, defaultdict

from qa_testgen.domain.enums import ScenarioType, ValidationStatus
from qa_testgen.domain.models import (
    BDDScenario,
    Requirement,
    ScenarioValidationIssue,
    ScenarioValidationReport,
)


class ScenarioCoverageChecker:
    """Детерминированно контролирует покрытие каждого требования всеми типами."""

    required_types: tuple[ScenarioType, ...] = tuple(ScenarioType)

    def find_missing_types(
        self,
        requirements: list[Requirement],
        scenarios: list[BDDScenario],
    ) -> dict[str, list[ScenarioType]]:
        actual_types: dict[str, set[ScenarioType]] = defaultdict(set)
        for scenario in scenarios:
            actual_types[scenario.requirement_id].add(scenario.scenario_type)

        missing: dict[str, list[ScenarioType]] = {}
        for requirement in requirements:
            missing_for_requirement = [
                scenario_type
                for scenario_type in self.required_types
                if scenario_type not in actual_types[requirement.id]
            ]
            if missing_for_requirement:
                missing[requirement.id] = missing_for_requirement
        return missing

    def enforce_coverage(
        self,
        requirements: list[Requirement],
        scenarios: list[BDDScenario],
        report: ScenarioValidationReport,
    ) -> ScenarioValidationReport:
        missing_types = self.find_missing_types(requirements, scenarios)
        requirement_ids = {item.id for item in requirements}
        unknown_scenarios = [
            item for item in scenarios if item.requirement_id not in requirement_ids
        ]
        id_counts = Counter(item.id for item in scenarios)
        duplicate_ids = [
            scenario_id for scenario_id, count in id_counts.items() if count > 1
        ]
        if not missing_types and not unknown_scenarios and not duplicate_ids:
            return report

        issues = list(report.issues)
        recommendations = list(report.recommendations)
        existing_messages = {issue.message for issue in issues}
        total_required = len(requirements) * len(self.required_types)
        total_missing = sum(len(types) for types in missing_types.values())

        for requirement_id, types in missing_types.items():
            type_names = ", ".join(item.value for item in types)
            message = (
                f"Requirement {requirement_id} is missing scenario types: {type_names}."
            )
            recommendation = (
                f"Add distinct {type_names} scenarios for requirement {requirement_id}."
            )
            if message not in existing_messages:
                issues.append(
                    ScenarioValidationIssue(
                        severity="high",
                        scenario_id=None,
                        requirement_id=requirement_id,
                        message=message,
                        recommendation=recommendation,
                    )
                )
            if recommendation not in recommendations:
                recommendations.append(recommendation)

        for scenario in unknown_scenarios:
            message = (
                f"Scenario {scenario.id} references unknown requirement "
                f"{scenario.requirement_id}."
            )
            recommendation = (
                f"Remove scenario {scenario.id} or bind it to an existing "
                "requirement_id."
            )
            if message not in existing_messages:
                issues.append(
                    ScenarioValidationIssue(
                        severity="high",
                        scenario_id=scenario.id,
                        requirement_id=scenario.requirement_id,
                        message=message,
                        recommendation=recommendation,
                    )
                )
            if recommendation not in recommendations:
                recommendations.append(recommendation)

        if duplicate_ids:
            duplicate_names = ", ".join(duplicate_ids)
            message = f"Duplicate scenario IDs found: {duplicate_names}."
            recommendation = "Assign a unique id to every BDD scenario."
            if message not in existing_messages:
                issues.append(
                    ScenarioValidationIssue(
                        severity="high",
                        scenario_id=None,
                        requirement_id=None,
                        message=message,
                        recommendation=recommendation,
                    )
                )
            if recommendation not in recommendations:
                recommendations.append(recommendation)

        scenario_requirement_ids = {item.requirement_id for item in scenarios}
        fully_missing = [
            item.id for item in requirements if item.id not in scenario_requirement_ids
        ]
        coverage_score = (
            (total_required - total_missing) / total_required
            if total_required
            else 0.0
        )
        status = (
            ValidationStatus.INVALID
            if fully_missing
            or unknown_scenarios
            or report.status == ValidationStatus.INVALID
            else ValidationStatus.NEEDS_REVISION
        )
        return report.model_copy(
            update={
                "status": status,
                "score": min(report.score, coverage_score),
                "issues": issues,
                "missing_requirements": list(
                    dict.fromkeys([*report.missing_requirements, *fully_missing])
                ),
                "duplicated_scenarios": list(
                    dict.fromkeys([*report.duplicated_scenarios, *duplicate_ids])
                ),
                "recommendations": recommendations,
            }
        )
