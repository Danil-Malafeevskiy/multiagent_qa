import json
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from qa_testgen.domain.models import PipelineResult
from qa_testgen.domain.state import GraphState
from qa_testgen.services.metrics import MetricsCalculator


class ArtifactStore:
    def __init__(self, artifacts_dir: Path) -> None:
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.run_dir: Path | None = None

    def create_run_dir(self) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
        self.run_dir = self.artifacts_dir / f"run_{timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=False)
        return self.run_dir

    def save_json(self, path: Path, data: Any) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
                default=self._json_default,
            ),
            encoding="utf-8",
        )
        return str(path)

    def save_text(self, path: Path, content: str) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def save_pipeline_artifacts(self, state: GraphState) -> dict[str, str]:
        run_dir = self.run_dir or self.create_run_dir()
        pytest_result = state["pytest_generation_result"]
        paths = {
            "source_code": self.save_json(
                run_dir / "source_code.json", state["source_code"]
            ),
            "requirements": self.save_json(
                run_dir / "requirements.json", state["requirements"]
            ),
            "scenarios": self.save_json(run_dir / "scenarios.json", state["scenarios"]),
            "scenario_generation_notes": self.save_text(
                run_dir / "scenario_generation_notes.txt",
                state["scenario_generation_notes"],
            ),
            "scenario_validation_report": self.save_json(
                run_dir / "scenario_validation_report.json",
                state["scenario_validation_report"],
            ),
            "generated_tests": self.save_text(
                run_dir / "generated_tests.py",
                pytest_result.test_code if pytest_result else "",
            ),
            "syntax_validation_result": self.save_json(
                run_dir / "syntax_validation_result.json",
                state["syntax_validation_result"],
            ),
            "errors": self.save_json(run_dir / "errors.json", state["errors"]),
            "metrics": self.save_json(
                run_dir / "metrics.json",
                MetricsCalculator().calculate_proposed_metrics(state),
            ),
        }
        pipeline_result = PipelineResult(
            requirements=state["requirements"],
            scenarios=state["scenarios"],
            scenario_generation_notes=state["scenario_generation_notes"],
            validation_report=state["scenario_validation_report"],
            pytest_result=pytest_result,
            syntax_result=state["syntax_validation_result"],
            artifacts_path=str(run_dir),
        )
        paths["pipeline_result"] = self.save_json(
            run_dir / "pipeline_result.json", pipeline_result
        )
        return paths

    @staticmethod
    def _json_default(value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, Enum):
            return value.value
        raise TypeError(
            f"Object of type {type(value).__name__} is not JSON serializable"
        )
