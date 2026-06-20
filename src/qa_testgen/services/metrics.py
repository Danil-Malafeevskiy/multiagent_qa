from collections import Counter
from typing import Any

from qa_testgen.domain.enums import PipelineType, ScenarioType
from qa_testgen.domain.state import GraphState


class MetricsCalculator:
    def calculate_metrics(self, state: GraphState) -> dict[str, Any]:
        if state["pipeline_type"] == PipelineType.BASELINE:
            return self.calculate_baseline_metrics(state)
        return self.calculate_proposed_metrics(state)

    def calculate_proposed_metrics(self, state: GraphState) -> dict[str, Any]:
        scenarios = state["scenarios"]
        requirement_ids = {item.id for item in state["requirements"]}
        covered_ids = {item.requirement_id for item in scenarios}
        type_counts = Counter(item.scenario_type.value for item in scenarios)

        return {
            "pipeline_type": PipelineType.PROPOSED.value,
            "syntax_validity": int(
                bool(
                    state["syntax_validation_result"]
                    and state["syntax_validation_result"].is_valid
                )
            ),
            "requirement_coverage_estimate": (
                len(requirement_ids & covered_ids) / len(requirement_ids)
                if requirement_ids
                else 0.0
            ),
            "scenario_type_distribution": {
                scenario_type.value: type_counts.get(scenario_type.value, 0)
                for scenario_type in ScenarioType
            },
            "oracle_presence_rate": (
                sum(
                    bool(
                        item.oracle.description
                        and item.oracle.assertion_intent
                        and item.oracle.expected_result
                    )
                    for item in scenarios
                )
                / len(scenarios)
                if scenarios
                else 0.0
            ),
            "average_scenarios_per_requirement": (
                len(scenarios) / len(requirement_ids) if requirement_ids else 0.0
            ),
            "generation_attempts": {
                "scenario_validation_attempt": state["scenario_validation_attempt"],
                "test_generation_attempt": state["test_generation_attempt"],
            },
        }

    def calculate_baseline_metrics(self, state: GraphState) -> dict[str, Any]:
        requirement_ids = {item.id for item in state["requirements"]}
        pytest_result = state["pytest_generation_result"]
        test_code = pytest_result.test_code if pytest_result else ""
        covered_ids = {
            requirement_id
            for requirement_id in requirement_ids
            if requirement_id.casefold() in test_code.casefold()
        }
        syntax_result = state["syntax_validation_result"]
        return {
            "pipeline_type": PipelineType.BASELINE.value,
            "syntax_validity": int(bool(syntax_result and syntax_result.is_valid)),
            "requirement_coverage_estimate": (
                len(covered_ids) / len(requirement_ids) if requirement_ids else 0.0
            ),
            "scenario_type_distribution": {
                scenario_type.value: 0 for scenario_type in ScenarioType
            },
            "oracle_presence_rate": 0.0,
            "average_scenarios_per_requirement": 0.0,
            "generation_attempts": {
                "scenario_validation_attempt": 0,
                "test_generation_attempt": state["test_generation_attempt"],
            },
        }

    def evaluate_oracle_quality_later(self) -> None:
        """Reserved for a future semantic or LLM-based oracle assessment."""
        raise NotImplementedError
