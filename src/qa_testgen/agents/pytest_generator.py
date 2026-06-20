from pydantic import BaseModel, ValidationError

from qa_testgen.agents.base import AgentExecutionError, BaseAgent
from qa_testgen.config.settings import AppSettings
from qa_testgen.domain.models import (
    BDDScenario,
    PytestGenerationResult,
    ScenarioValidationReport,
    SourceCodeInput,
    SyntaxValidationResult,
)
from qa_testgen.llm.base import BaseLLMClient
from qa_testgen.prompts.pytest_prompts import (
    PYTEST_GENERATOR_SYSTEM_PROMPT,
    PYTEST_REPAIR_SYSTEM_PROMPT,
    build_pytest_generation_user_prompt,
    build_pytest_repair_user_prompt,
)


class PytestGeneratorInput(BaseModel):
    source_code: SourceCodeInput
    scenarios: list[BDDScenario]
    validation_report: ScenarioValidationReport | None = None


class PytestRepairInput(BaseModel):
    source_code: SourceCodeInput
    scenarios: list[BDDScenario]
    previous_test_code: str
    syntax_error: SyntaxValidationResult


class PytestGeneratorAgent(BaseAgent[PytestGeneratorInput, PytestGenerationResult]):
    def __init__(self, llm_client: BaseLLMClient, settings: AppSettings) -> None:
        super().__init__(llm_client, settings, "pytest_generator")

    def run(self, input_data: PytestGeneratorInput) -> PytestGenerationResult:
        self._log_start(scenarios=len(input_data.scenarios), mode="generation")
        raw = self.llm_client.invoke_json(
            self._build_system_prompt(), self._build_user_prompt(input_data)
        )
        result = self._validate_result(raw)
        self._log_finish(
            scenarios=len(input_data.scenarios), test_code_length=len(result.test_code)
        )
        return result

    def repair(self, input_data: PytestRepairInput) -> PytestGenerationResult:
        self._log_start(scenarios=len(input_data.scenarios), mode="repair")
        raw = self.llm_client.invoke_json(
            PYTEST_REPAIR_SYSTEM_PROMPT,
            build_pytest_repair_user_prompt(
                input_data.source_code,
                input_data.scenarios,
                input_data.previous_test_code,
                input_data.syntax_error,
            ),
        )
        result = self._validate_result(raw)
        self._log_finish(test_code_length=len(result.test_code), mode="repair")
        return result

    def _build_system_prompt(self) -> str:
        return PYTEST_GENERATOR_SYSTEM_PROMPT

    def _build_user_prompt(self, input_data: PytestGeneratorInput) -> str:
        return build_pytest_generation_user_prompt(
            input_data.source_code,
            input_data.scenarios,
            input_data.validation_report,
        )

    @staticmethod
    def _validate_result(raw: dict[str, object]) -> PytestGenerationResult:
        try:
            return PytestGenerationResult.model_validate(raw)
        except ValidationError as exc:
            raise AgentExecutionError(
                f"Pytest generator returned an invalid schema: {exc}"
            ) from exc
