import json

from qa_testgen.domain.models import (
    BDDScenario,
    Requirement,
    ScenarioValidationReport,
    SourceCodeInput,
)

SCENARIO_VALIDATOR_SYSTEM_PROMPT = """Ты — LLM-агент-критик и валидатор BDD-сценариев.
Для каждого требования обязательно проверь наличие всех пяти типов: positive, negative, boundary, edge и error_handling. Если отсутствует хотя бы один тип хотя бы у одного requirement_id, status не может быть valid.
Проверь дубли, противоречия требованиям и коду, силу oracle, пригодность для pytest и отсутствие выдуманной бизнес-логики. Сценарии разных типов должны проверять различные условия.
Если передан previous_validation_report, отдельно проверь, что новая версия сценариев действительно устранила каждый предыдущий issue и выполнила каждую recommendation. Любую неучтённую рекомендацию повтори в issues и recommendations и верни needs_revision или invalid.
Ты не исправляешь сценарии, а только оцениваешь их и даёшь конкретные рекомендации.
Верни строго JSON формата ScenarioValidationReport: status (valid, invalid или needs_revision), score от 0 до 1, issues, missing_requirements, duplicated_scenarios, recommendations. Никакого markdown и текста вне JSON."""


def build_scenario_validation_user_prompt(
    source_code: SourceCodeInput,
    requirements: list[Requirement],
    scenarios: list[BDDScenario],
    previous_validation_report: ScenarioValidationReport | None = None,
) -> str:
    payload = {
        "source_code": source_code.model_dump(mode="json"),
        "requirements": [item.model_dump(mode="json") for item in requirements],
        "scenarios": [item.model_dump(mode="json") for item in scenarios],
        "previous_validation_report_to_verify": (
            previous_validation_report.model_dump(mode="json")
            if previous_validation_report
            else None
        ),
        "required_types_per_requirement": [
            "positive",
            "negative",
            "boundary",
            "edge",
            "error_handling",
        ],
    }
    return "Проверь следующие данные:\n" + json.dumps(
        payload, ensure_ascii=False, indent=2
    )
