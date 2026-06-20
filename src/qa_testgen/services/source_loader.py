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
            if any(part in self._IGNORED_DIRECTORIES for part in path.parts):
                continue
            files[path.relative_to(project_dir).as_posix()] = path.read_text(
                encoding="utf-8"
            )
        if not files:
            raise ValueError(f"No Python files found in: {project_dir}")
        return SourceCodeInput(project_name=project_dir.name, files=files)

    def load_requirements(self, requirements_file: Path) -> list[Requirement]:
        if not requirements_file.is_file():
            raise ValueError(f"Requirements file does not exist: {requirements_file}")
        requirements: list[Requirement] = []
        generated_index = 1
        for raw_line in requirements_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip().lstrip("-* ").strip()
            if not line or line.startswith("#"):
                continue
            match = self._REQUIREMENT_PATTERN.match(line)
            if match:
                requirement_id, text = match.groups()
            else:
                requirement_id = f"REQ-{generated_index:03d}"
                text = line
                generated_index += 1
            requirements.append(
                Requirement(id=requirement_id, text=text, priority=None, tags=[])
            )
        if not requirements:
            raise ValueError(f"No requirements found in: {requirements_file}")
        return requirements
