import json

from qa_testgen.domain.models import (
    BDDScenario,
    Requirement,
    ScenarioValidationReport,
    SourceCodeInput,
    SyntaxValidationResult,
)

PYTEST_GENERATOR_SYSTEM_PROMPT = """Ты — LLM-агент генерации pytest-тестов. Строго преобразуй валидированные BDD-сценарии в исполняемый pytest-код.
Не генерируй BDD, markdown или объяснения вне JSON. Не выдумывай API. Каждый тест свяжи с requirement_id и scenario_id в имени или комментарии. Используй Arrange / Act / Assert и конкретный oracle; при ошибках используй pytest.raises.
Верни JSON PytestGenerationResult с полями requirement_id, scenario_ids, test_code, imports, notes. test_code должен быть синтаксически валидным Python."""

PYTEST_REPAIR_SYSTEM_PROMPT = """Ты — LLM-агент исправления pytest-кода. Исправь указанную синтаксическую ошибку, сохрани соответствие BDD и смысл всех проверок. Не добавляй бизнес-логику и не выдумывай API.
Верни строго JSON PytestGenerationResult с полями requirement_id, scenario_ids, test_code, imports, notes, без markdown и текста вне JSON."""

DIRECT_PYTEST_BASELINE_SYSTEM_PROMPT = """Ты — LLM-агент прямой генерации pytest-тестов. По требованиям и исходному Python-коду сгенерируй тесты без BDD.
Используй только существующий API, Arrange / Act / Assert, конкретные ожидаемые результаты и pytest.raises для ошибок. Связывай тесты с requirement_id. Верни строго JSON PytestGenerationResult без markdown."""


def _serialize(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_pytest_generation_user_prompt(
    source_code: SourceCodeInput,
    scenarios: list[BDDScenario],
    validation_report: ScenarioValidationReport | None,
) -> str:
    return "Сгенерируй тесты по данным:\n" + _serialize(
        {
            "source_code": source_code.model_dump(mode="json"),
            "scenarios": [item.model_dump(mode="json") for item in scenarios],
            "validation_report": (
                validation_report.model_dump(mode="json") if validation_report else None
            ),
        }
    )


def build_pytest_repair_user_prompt(
    source_code: SourceCodeInput,
    scenarios: list[BDDScenario],
    previous_test_code: str,
    syntax_error: SyntaxValidationResult,
) -> str:
    return "Исправь тесты по данным:\n" + _serialize(
        {
            "source_code": source_code.model_dump(mode="json"),
            "scenarios": [item.model_dump(mode="json") for item in scenarios],
            "previous_test_code": previous_test_code,
            "syntax_error": syntax_error.model_dump(mode="json"),
        }
    )


def build_baseline_user_prompt(
    source_code: SourceCodeInput, requirements: list[Requirement]
) -> str:
    return "Сгенерируй тесты по данным:\n" + _serialize(
        {
            "source_code": source_code.model_dump(mode="json"),
            "requirements": [item.model_dump(mode="json") for item in requirements],
        }
    )
