from pydantic import BaseModel

from qa_testgen.agents.base import BaseAgent
from qa_testgen.config.settings import AppSettings
from qa_testgen.domain.models import (
    BDDScenario,
    Requirement,
    ScenarioValidationReport,
    SourceCodeInput,
)
from qa_testgen.llm.base import BaseLLMClient
from qa_testgen.prompts.validation_prompts import (
    SCENARIO_VALIDATOR_SYSTEM_PROMPT,
    build_scenario_validation_user_prompt,
)
from qa_testgen.services.scenario_coverage import ScenarioCoverageChecker


class ScenarioValidatorInput(BaseModel):
    source_code: SourceCodeInput
    requirements: list[Requirement]
    scenarios: list[BDDScenario]
    previous_validation_report: ScenarioValidationReport | None = None


class ScenarioValidatorAgent(
    BaseAgent[ScenarioValidatorInput, ScenarioValidationReport]
):
    def __init__(
        self,
        llm_client: BaseLLMClient,
        settings: AppSettings,
        coverage_checker: ScenarioCoverageChecker | None = None,
    ) -> None:
        super().__init__(llm_client, settings, "scenario_validator")
        self.coverage_checker = coverage_checker or ScenarioCoverageChecker()

    def run(self, input_data: ScenarioValidatorInput) -> ScenarioValidationReport:
        self._log_start(scenarios=len(input_data.scenarios))
        result = self._invoke_model(
            self._build_system_prompt(),
            self._build_user_prompt(input_data),
            ScenarioValidationReport,
        )
        result = self.coverage_checker.enforce_coverage(
            input_data.requirements, input_data.scenarios, result
        )
        self._log_finish(
            status=result.status,
            score=result.score,
            issues=len(result.issues),
            missing_requirements=len(result.missing_requirements),
            duplicated_scenarios=len(result.duplicated_scenarios),
        )
        return result

    def _build_system_prompt(self) -> str:
        return SCENARIO_VALIDATOR_SYSTEM_PROMPT

    def _build_user_prompt(self, input_data: ScenarioValidatorInput) -> str:
        return build_scenario_validation_user_prompt(
            input_data.source_code,
            input_data.requirements,
            input_data.scenarios,
            input_data.previous_validation_report,
        )
