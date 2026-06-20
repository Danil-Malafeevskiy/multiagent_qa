from qa_testgen.domain.enums import PipelineType
from qa_testgen.services.metrics import MetricsCalculator
from tests.factories import make_graph_state


def test_baseline_metrics_use_requirement_ids_from_test_code() -> None:
    state = make_graph_state(PipelineType.BASELINE)

    metrics = MetricsCalculator().calculate_metrics(state)

    assert metrics["pipeline_type"] == "baseline"
    assert metrics["requirement_coverage_estimate"] == 1.0
    assert metrics["syntax_validity"] == 1
    assert sum(metrics["scenario_type_distribution"].values()) == 0

