import json
from pathlib import Path

from qa_testgen.domain.enums import PipelineType
from qa_testgen.services.artifact_store import ArtifactStore
from tests.factories import make_graph_state


def test_artifact_store_saves_json_and_text(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    run_dir = store.create_run_dir()

    json_path = store.save_json(run_dir / "data.json", {"message": "тест"})
    text_path = store.save_text(run_dir / "generated_tests.py", "assert True\n")

    assert json.loads(Path(json_path).read_text(encoding="utf-8")) == {
        "message": "тест"
    }
    assert Path(text_path).read_text(encoding="utf-8") == "assert True\n"


def test_pipeline_artifacts_include_metadata_histories_and_unique_runs(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(
        tmp_path,
        run_metadata={"pipeline_type": "baseline", "llm_model": "fake"},
    )
    state = make_graph_state(PipelineType.BASELINE)

    first = store.save_pipeline_artifacts(state)
    second = store.save_pipeline_artifacts(state)

    assert Path(first["pipeline_result"]).parent != Path(
        second["pipeline_result"]
    ).parent
    metadata = json.loads(Path(first["run_metadata"]).read_text(encoding="utf-8"))
    metrics = json.loads(Path(first["metrics"]).read_text(encoding="utf-8"))
    assert metadata == {"pipeline_type": "baseline", "llm_model": "fake"}
    assert metrics["pipeline_type"] == "baseline"
    assert Path(first["scenario_generation_history"]).exists()
    assert Path(first["scenario_validation_history"]).exists()
