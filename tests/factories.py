from qa_testgen.domain.enums import PipelineType
from qa_testgen.domain.models import (
    PytestGenerationResult,
    Requirement,
    SourceCodeInput,
    SyntaxValidationResult,
)
from qa_testgen.domain.state import GraphState


def make_graph_state(
    pipeline_type: PipelineType = PipelineType.PROPOSED,
) -> GraphState:
    return {
        "pipeline_type": pipeline_type,
        "source_code": SourceCodeInput(
            project_name="sample", files={"app.py": "def value(): return 1"}
        ),
        "requirements": [Requirement(id="REQ-001", text="Return one")],
        "scenarios": [],
        "scenario_generation_notes": "",
        "scenario_generation_history": [],
        "scenario_validation_report": None,
        "scenario_validation_history": [],
        "pytest_generation_result": PytestGenerationResult(
            requirement_id="REQ-001",
            scenario_ids=[],
            test_code="# REQ-001\ndef test_value():\n    assert 1 == 1\n",
            imports=[],
            notes="",
        ),
        "syntax_validation_result": SyntaxValidationResult(is_valid=True),
        "scenario_validation_attempt": 0,
        "test_generation_attempt": 1,
        "errors": [],
        "artifacts": {},
    }

