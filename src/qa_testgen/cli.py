import json
import logging
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console
from rich.table import Table

from qa_testgen.agents.baseline_generator import (
    BaselineGeneratorInput,
    BaselinePytestGeneratorAgent,
)
from qa_testgen.agents.pytest_generator import PytestGeneratorAgent
from qa_testgen.agents.scenario_generator import ScenarioGeneratorAgent
from qa_testgen.agents.scenario_validator import ScenarioValidatorAgent
from qa_testgen.agents.syntax_validator import SyntaxValidatorAgent
from qa_testgen.config.settings import AppSettings, get_settings
from qa_testgen.domain.enums import PipelineType
from qa_testgen.domain.models import Requirement, SourceCodeInput
from qa_testgen.domain.state import GraphState
from qa_testgen.graph.builder import TestGenerationGraphBuilder
from qa_testgen.llm.openai_client import create_llm_client
from qa_testgen.services.artifact_store import ArtifactStore
from qa_testgen.services.source_loader import SourceLoader
from qa_testgen.services.syntax_checker import SyntaxChecker

app = typer.Typer(help="Multi-agent pytest generation research prototype")
console = Console()


def _settings_with_output(output_dir: Path | None) -> AppSettings:
    settings = get_settings()
    if output_dir is None:
        return settings
    output_dir.mkdir(parents=True, exist_ok=True)
    return settings.model_copy(update={"artifacts_dir": output_dir})


def _configure_logging(settings: AppSettings) -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _load_inputs(
    project_dir: Path, requirements_file: Path
) -> tuple[SourceCodeInput, list[Requirement]]:
    loader = SourceLoader()
    return (
        loader.load_python_project(project_dir),
        loader.load_requirements(requirements_file),
    )


def _artifact_store(
    settings: AppSettings, pipeline_type: PipelineType
) -> ArtifactStore:
    metadata = settings.model_dump(mode="json", exclude={"openai_api_key"})
    metadata["pipeline_type"] = pipeline_type.value
    return ArtifactStore(settings.artifacts_dir, run_metadata=metadata)


@app.command("run-proposed")
def run_proposed(
    project_dir: Annotated[Path, typer.Option(exists=True, file_okay=False)],
    requirements_file: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
    output_dir: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Run BDD generation, validation, pytest generation and syntax validation."""
    settings = _settings_with_output(output_dir)
    _configure_logging(settings)
    source_code, requirements = _load_inputs(project_dir, requirements_file)
    llm_client = create_llm_client(settings)
    syntax_validator = SyntaxValidatorAgent(SyntaxChecker())
    graph = TestGenerationGraphBuilder(
        ScenarioGeneratorAgent(llm_client, settings),
        ScenarioValidatorAgent(llm_client, settings),
        PytestGeneratorAgent(llm_client, settings),
        syntax_validator,
        settings,
        _artifact_store(settings, PipelineType.PROPOSED),
    ).build()
    initial_state: GraphState = {
        "pipeline_type": PipelineType.PROPOSED,
        "source_code": source_code,
        "requirements": requirements,
        "scenarios": [],
        "scenario_generation_notes": "",
        "scenario_generation_history": [],
        "scenario_validation_report": None,
        "scenario_validation_history": [],
        "pytest_generation_result": None,
        "syntax_validation_result": None,
        "scenario_validation_attempt": 0,
        "test_generation_attempt": 0,
        "errors": [],
        "artifacts": {},
    }
    console.print("[bold]Запуск proposed workflow...[/bold]")
    result = cast(GraphState, graph.invoke(initial_state))
    syntax_result = result["syntax_validation_result"]
    console.print(f"Сценариев: [cyan]{len(result['scenarios'])}[/cyan]")
    console.print(
        "Синтаксис: "
        + (
            "[green]valid[/green]"
            if syntax_result and syntax_result.is_valid
            else "[red]invalid[/red]"
        )
    )
    console.print(f"Артефакты: [cyan]{_artifact_directory(result)}[/cyan]")


@app.command("run-baseline")
def run_baseline(
    project_dir: Annotated[Path, typer.Option(exists=True, file_okay=False)],
    requirements_file: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
    output_dir: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Run direct requirement-to-pytest generation."""
    settings = _settings_with_output(output_dir)
    _configure_logging(settings)
    source_code, requirements = _load_inputs(project_dir, requirements_file)
    llm_client = create_llm_client(settings)
    pytest_result = BaselinePytestGeneratorAgent(llm_client, settings).run(
        BaselineGeneratorInput(source_code=source_code, requirements=requirements)
    )
    syntax_result = SyntaxValidatorAgent(SyntaxChecker()).run(pytest_result.test_code)
    state: GraphState = {
        "pipeline_type": PipelineType.BASELINE,
        "source_code": source_code,
        "requirements": requirements,
        "scenarios": [],
        "scenario_generation_notes": "Baseline does not generate BDD scenarios.",
        "scenario_generation_history": [],
        "scenario_validation_report": None,
        "scenario_validation_history": [],
        "pytest_generation_result": pytest_result,
        "syntax_validation_result": syntax_result,
        "scenario_validation_attempt": 0,
        "test_generation_attempt": 1,
        "errors": [],
        "artifacts": {},
    }
    state["artifacts"] = _artifact_store(
        settings, PipelineType.BASELINE
    ).save_pipeline_artifacts(state)
    console.print("Baseline generation: [green]done[/green]")
    console.print(
        "Синтаксис: "
        + ("[green]valid[/green]" if syntax_result.is_valid else "[red]invalid[/red]")
    )
    console.print(f"Артефакты: [cyan]{_artifact_directory(state)}[/cyan]")


@app.command()
def compare(
    artifacts_dir: Annotated[Path, typer.Option(exists=True, file_okay=False)] = Path(
        "artifacts"
    ),
) -> None:
    """Show metrics available for artifact runs."""
    table = Table("Run", "Type", "Model", "Syntax", "Coverage", "Scenarios")
    for run_dir in sorted(artifacts_dir.glob("run_*")):
        metrics_path = run_dir / "metrics.json"
        if not metrics_path.exists():
            continue
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        metadata_path = run_dir / "run_metadata.json"
        metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.exists()
            else {}
        )
        table.add_row(
            run_dir.name,
            str(metrics.get("pipeline_type", metadata.get("pipeline_type", "-"))),
            str(metadata.get("llm_model", "-")),
            str(metrics.get("syntax_validity", "-")),
            f"{metrics.get('requirement_coverage_estimate', 0):.2f}",
            str(sum(metrics.get("scenario_type_distribution", {}).values())),
        )
    console.print(table)


def _artifact_directory(state: GraphState) -> str:
    pipeline_path = state["artifacts"].get("pipeline_result", "")
    return str(Path(pipeline_path).parent) if pipeline_path else "unknown"


if __name__ == "__main__":
    app()
