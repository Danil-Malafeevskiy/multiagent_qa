from pathlib import Path

import pytest

from qa_testgen.services.source_loader import SourceLoader


def test_load_requirements_with_and_without_ids(tmp_path: Path) -> None:
    requirements_file = tmp_path / "requirements.md"
    requirements_file.write_text(
        "# Requirements\nREQ-CART: Add an item\nReject an empty order\n",
        encoding="utf-8",
    )

    requirements = SourceLoader().load_requirements(requirements_file)

    assert [item.id for item in requirements] == ["REQ-CART", "REQ-001"]
    assert requirements[1].text == "Reject an empty order"


def test_load_python_project_ignores_tests(tmp_path: Path) -> None:
    project_dir = tmp_path / "shop"
    project_dir.mkdir()
    (project_dir / "cart.py").write_text("class Cart:\n    pass\n", encoding="utf-8")
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_cart.py").write_text("assert False\n", encoding="utf-8")

    source = SourceLoader().load_python_project(project_dir)

    assert source.project_name == "shop"
    assert list(source.files) == ["cart.py"]


def test_load_python_project_rejects_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No Python files"):
        SourceLoader().load_python_project(tmp_path)


def test_project_named_tests_is_not_ignored(tmp_path: Path) -> None:
    project_dir = tmp_path / "tests"
    project_dir.mkdir()
    (project_dir / "app.py").write_text("VALUE = 1\n", encoding="utf-8")

    source = SourceLoader().load_python_project(project_dir)

    assert list(source.files) == ["app.py"]


def test_generated_requirement_id_does_not_collide_with_explicit_id(
    tmp_path: Path,
) -> None:
    requirements_file = tmp_path / "requirements.md"
    requirements_file.write_text(
        "Requirement without id\nREQ-001: Explicit requirement\n",
        encoding="utf-8",
    )

    requirements = SourceLoader().load_requirements(requirements_file)

    assert [item.id for item in requirements] == ["REQ-002", "REQ-001"]


def test_duplicate_explicit_requirement_ids_are_rejected(tmp_path: Path) -> None:
    requirements_file = tmp_path / "requirements.md"
    requirements_file.write_text(
        "REQ-001: First\nREQ-001: Second\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate requirement IDs"):
        SourceLoader().load_requirements(requirements_file)
