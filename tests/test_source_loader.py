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
