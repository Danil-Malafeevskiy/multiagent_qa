import json
from pathlib import Path

from qa_testgen.services.artifact_store import ArtifactStore


def test_artifact_store_saves_json_and_text(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    run_dir = store.create_run_dir()

    json_path = store.save_json(run_dir / "data.json", {"message": "тест"})
    text_path = store.save_text(run_dir / "generated_tests.py", "assert True\n")

    assert json.loads(Path(json_path).read_text(encoding="utf-8")) == {
        "message": "тест"
    }
    assert Path(text_path).read_text(encoding="utf-8") == "assert True\n"
