import json

from qa_testgen.domain.models import (
    BDDScenario,
    Requirement,
    ScenarioValidationReport,
    SourceCodeInput,
)

SCENARIO_GENERATOR_SYSTEM_PROMPT = """Ты — LLM-агент генерации тестовых BDD-сценариев для Python-приложения.
Создай человеко-читаемые сценарии по требованиям и реальному исходному коду. Не генерируй pytest.
Для КАЖДОГО requirement_id обязательно создай минимум по одному сценарию КАЖДОГО типа: positive, negative, boundary, edge и error_handling. Таким образом, каждое требование должно иметь не менее пяти разнотипных сценариев.
Сценарии разных типов должны проверять разные условия, а не дублировать один случай с другим названием. Используй только поведение, подтверждённое требованием или исходным кодом. Для edge и error_handling ищи экстремальные значения, некорректные входы, исключения и устойчивость состояния объекта.
Каждый объект сценария обязан содержать точные поля id, requirement_id, title, scenario_type, steps, oracle, covered_conditions, test_data и rationale.
scenario_type — ровно одно из: positive, negative, boundary, edge, error_handling.
steps — JSON-массив объектов с полями keyword и text. Обязательны отдельные шаги Given, When и Then. Нельзя заменять массив steps полями given, when или then.
oracle обязан содержать description, assertion_intent и expected_result. Нельзя пропускать description.
generation_notes — одна строка, а не массив строк.
Если передан previous_validation_report, это режим ревизии. Верни ПОЛНЫЙ обновлённый набор сценариев: сохрани корректные предыдущие сценарии, исправь каждый issue, выполни каждую recommendation, добавь missing_requirements и недостающие типы, удали duplicated_scenarios. В generation_notes перечисли, как учтена каждая рекомендация. Нельзя игнорировать ни одну рекомендацию.
Не придумывай поведение и API. Неоднозначность фиксируй в rationale. Сценарии должны быть конкретными и пригодными для генерации pytest.
Верни строго JSON, соответствующий переданной JSON Schema. Никакого markdown и текста вне JSON."""


def build_scenario_generation_user_prompt(
    source_code: SourceCodeInput,
    requirements: list[Requirement],
    previous_scenarios: list[BDDScenario] | None = None,
    validation_report: ScenarioValidationReport | None = None,
) -> str:
    recommendations = []
    if validation_report is not None:
        recommendations = [
            *validation_report.recommendations,
            *(issue.recommendation for issue in validation_report.issues),
        ]
    payload = {
        "requirements": [item.model_dump(mode="json") for item in requirements],
        "source_code": source_code.model_dump(mode="json"),
        "previous_scenarios": [
            item.model_dump(mode="json") for item in (previous_scenarios or [])
        ],
        "previous_validation_report": (
            validation_report.model_dump(mode="json") if validation_report else None
        ),
        "mandatory_recommendations_to_address": list(dict.fromkeys(recommendations)),
        "coverage_policy": {
            "required_types_per_requirement": [
                "positive",
                "negative",
                "boundary",
                "edge",
                "error_handling",
            ],
            "return_mode": "full_revised_scenario_set",
        },
    }
    return "Входные данные:\n" + json.dumps(payload, ensure_ascii=False, indent=2)
