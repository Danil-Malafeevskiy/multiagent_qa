from pydantic import BaseModel

from qa_testgen.agents.base import BaseAgent
from qa_testgen.config.settings import AppSettings
from qa_testgen.domain.models import (
    PytestGenerationResult,
    Requirement,
    SourceCodeInput,
)
from qa_testgen.llm.base import BaseLLMClient
from qa_testgen.prompts.pytest_prompts import (
    DIRECT_PYTEST_BASELINE_SYSTEM_PROMPT,
    build_baseline_user_prompt,
)


class BaselineGeneratorInput(BaseModel):
    source_code: SourceCodeInput
    requirements: list[Requirement]


class BaselinePytestGeneratorAgent(
    BaseAgent[BaselineGeneratorInput, PytestGenerationResult]
):
    def __init__(self, llm_client: BaseLLMClient, settings: AppSettings) -> None:
        super().__init__(llm_client, settings, "baseline_pytest_generator")

    def run(self, input_data: BaselineGeneratorInput) -> PytestGenerationResult:
        self._log_start(requirements=len(input_data.requirements))
        result = self._invoke_model(
            self._build_system_prompt(),
            self._build_user_prompt(input_data),
            PytestGenerationResult,
        )
        self._log_finish(test_code_length=len(result.test_code))
        return result

    def _build_system_prompt(self) -> str:
        return DIRECT_PYTEST_BASELINE_SYSTEM_PROMPT

    def _build_user_prompt(self, input_data: BaselineGeneratorInput) -> str:
        return build_baseline_user_prompt(
            input_data.source_code, input_data.requirements
        )
