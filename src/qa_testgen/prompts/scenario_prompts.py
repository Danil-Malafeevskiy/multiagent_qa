import json

from qa_testgen.domain.models import (
    Requirement,
    ScenarioValidationReport,
    SourceCodeInput,
)

SCENARIO_GENERATOR_SYSTEM_PROMPT = """Ты — LLM-агент генерации тестовых BDD-сценариев для Python-приложения.
Создай человеко-читаемые сценарии по требованиям и реальному исходному коду. Не генерируй pytest.
Создай от 1 до 3 содержательных сценариев для каждого requirement_id. Не создавай механически все типы: positive, negative, boundary, edge и error_handling нужны только когда они следуют из требования или кода.
Каждый объект сценария обязан содержать точные поля id, requirement_id, title, scenario_type, steps, oracle, covered_conditions, test_data и rationale.
scenario_type — ровно одно из: positive, negative, boundary, edge, error_handling.
steps — JSON-массив объектов с полями keyword и text. Обязательны отдельные шаги Given, When и Then. Нельзя заменять массив steps полями given, when или then.
oracle обязан содержать description, assertion_intent и expected_result. Нельзя пропускать description.
generation_notes — одна строка, а не массив строк.
Не придумывай поведение и API. Неоднозначность фиксируй в rationale. Сценарии должны быть пригодны для генерации pytest.
Верни строго JSON, соответствующий переданной JSON Schema. Никакого markdown и текста вне JSON."""


def build_scenario_generation_user_prompt(
    source_code: SourceCodeInput,
    requirements: list[Requirement],
    validation_report: ScenarioValidationReport | None = None,
) -> str:
    payload = {
        "requirements": [item.model_dump(mode="json") for item in requirements],
        "source_code": source_code.model_dump(mode="json"),
        "previous_validation_report": (
            validation_report.model_dump(mode="json") if validation_report else None
        ),
    }
    return "Входные данные:\n" + json.dumps(payload, ensure_ascii=False, indent=2)
