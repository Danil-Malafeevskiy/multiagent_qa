import json

from qa_testgen.domain.models import BDDScenario, Requirement, SourceCodeInput

SCENARIO_VALIDATOR_SYSTEM_PROMPT = """Ты — LLM-агент-критик и валидатор BDD-сценариев.
Проверь покрытие каждого требования, применимые позитивные, негативные и граничные случаи, дубли, противоречия требованиям и коду, силу oracle, пригодность для pytest и отсутствие выдуманной бизнес-логики. Не исправляй сценарии.
Верни строго JSON формата ScenarioValidationReport: status (valid, invalid или needs_revision), score от 0 до 1, issues, missing_requirements, duplicated_scenarios, recommendations. Никакого markdown и текста вне JSON."""


def build_scenario_validation_user_prompt(
    source_code: SourceCodeInput,
    requirements: list[Requirement],
    scenarios: list[BDDScenario],
) -> str:
    payload = {
        "source_code": source_code.model_dump(mode="json"),
        "requirements": [item.model_dump(mode="json") for item in requirements],
        "scenarios": [item.model_dump(mode="json") for item in scenarios],
    }
    return "Проверь следующие данные:\n" + json.dumps(
        payload, ensure_ascii=False, indent=2
    )
