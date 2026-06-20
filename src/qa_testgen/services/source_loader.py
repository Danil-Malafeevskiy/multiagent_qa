import re
from pathlib import Path

from qa_testgen.domain.models import Requirement, SourceCodeInput


class SourceLoader:
    _IGNORED_DIRECTORIES = {"__pycache__", ".venv", "venv", "tests", "artifacts"}
    _REQUIREMENT_PATTERN = re.compile(r"^(REQ-[A-Za-z0-9_-]+)\s*:\s*(.+)$")

    def load_python_project(self, project_dir: Path) -> SourceCodeInput:
        if not project_dir.is_dir():
            raise ValueError(f"Project directory does not exist: {project_dir}")
        files: dict[str, str] = {}
        for path in sorted(project_dir.rglob("*.py")):
            relative_path = path.relative_to(project_dir)
            if any(
                part in self._IGNORED_DIRECTORIES for part in relative_path.parts[:-1]
            ):
                continue
            files[relative_path.as_posix()] = path.read_text(encoding="utf-8")
        if not files:
            raise ValueError(f"No Python files found in: {project_dir}")
        return SourceCodeInput(project_name=project_dir.name, files=files)

    def load_requirements(self, requirements_file: Path) -> list[Requirement]:
        if not requirements_file.is_file():
            raise ValueError(f"Requirements file does not exist: {requirements_file}")
        parsed_lines: list[tuple[str | None, str]] = []
        for raw_line in requirements_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip().lstrip("-* ").strip()
            if not line or line.startswith("#"):
                continue
            match = self._REQUIREMENT_PATTERN.match(line)
            if match:
                requirement_id, text = match.groups()
                parsed_lines.append((requirement_id, text))
            else:
                parsed_lines.append((None, line))

        explicit_ids = [item[0] for item in parsed_lines if item[0] is not None]
        if len(explicit_ids) != len(set(explicit_ids)):
            raise ValueError("Duplicate requirement IDs found")

        requirements: list[Requirement] = []
        used_ids = set(explicit_ids)
        generated_index = 1
        for requirement_id, text in parsed_lines:
            if requirement_id is None:
                while f"REQ-{generated_index:03d}" in used_ids:
                    generated_index += 1
                requirement_id = f"REQ-{generated_index:03d}"
                used_ids.add(requirement_id)
                generated_index += 1
            requirements.append(
                Requirement(id=requirement_id, text=text, priority=None, tags=[])
            )
        if not requirements:
            raise ValueError(f"No requirements found in: {requirements_file}")
        return requirements
