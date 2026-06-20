from pydantic import BaseModel, ValidationError

from qa_testgen.agents.base import AgentExecutionError, BaseAgent
from qa_testgen.config.settings import AppSettings
from qa_testgen.domain.models import (
    Requirement,
    ScenarioGenerationResult,
    ScenarioValidationReport,
    SourceCodeInput,
)
from qa_testgen.llm.base import BaseLLMClient
from qa_testgen.prompts.scenario_prompts import (
    SCENARIO_GENERATOR_SYSTEM_PROMPT,
    build_scenario_generation_user_prompt,
)


class ScenarioGeneratorInput(BaseModel):
    source_code: SourceCodeInput
    requirements: list[Requirement]
    validation_report: ScenarioValidationReport | None = None


class ScenarioGeneratorAgent(
    BaseAgent[ScenarioGeneratorInput, ScenarioGenerationResult]
):
    def __init__(self, llm_client: BaseLLMClient, settings: AppSettings) -> None:
        super().__init__(llm_client, settings, "scenario_generator")

    def run(self, input_data: ScenarioGeneratorInput) -> ScenarioGenerationResult:
        self._log_start(requirements=len(input_data.requirements))
        raw = self.llm_client.invoke_json(
            self._build_system_prompt(), self._build_user_prompt(input_data)
        )
        try:
            result = ScenarioGenerationResult.model_validate(raw)
        except ValidationError as exc:
            raise AgentExecutionError(
                f"Scenario generator returned an invalid schema: {exc}"
            ) from exc
        self._log_finish(scenarios=len(result.scenarios))
        return result

    def _build_system_prompt(self) -> str:
        return SCENARIO_GENERATOR_SYSTEM_PROMPT

    def _build_user_prompt(self, input_data: ScenarioGeneratorInput) -> str:
        return build_scenario_generation_user_prompt(
            input_data.source_code,
            input_data.requirements,
            input_data.validation_report,
        )
