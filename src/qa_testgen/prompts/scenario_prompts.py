import json

from qa_testgen.domain.models import (
    Requirement,
    ScenarioValidationReport,
    SourceCodeInput,
)

SCENARIO_GENERATOR_SYSTEM_PROMPT = """Ты — LLM-агент генерации тестовых BDD-сценариев для Python-приложения.
Создай человеко-читаемые сценарии по требованиям и реальному исходному коду. Не генерируй pytest.
Для каждого requirement_id создай применимые positive, negative, boundary, edge и error_handling сценарии. Каждый сценарий обязан содержать Given/When/Then и oracle с описанием, assertion_intent и expected_result.
Не придумывай поведение и API. Неоднозначность фиксируй в rationale. Сценарии должны быть пригодны для генерации pytest.
Верни строго JSON, соответствующий ScenarioGenerationResult: объект с полями scenarios и generation_notes. Никакого markdown и текста вне JSON."""


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
