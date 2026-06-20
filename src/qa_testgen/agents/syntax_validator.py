import logging

from qa_testgen.domain.models import SyntaxValidationResult
from qa_testgen.services.syntax_checker import SyntaxChecker


class SyntaxValidatorAgent:
    """Детерминированный агент, который не выполняет LLM-вызовов."""

    def __init__(self, syntax_checker: SyntaxChecker) -> None:
        self.syntax_checker = syntax_checker
        self.logger = logging.getLogger("qa_testgen.agents.syntax_validator")

    def run(self, test_code: str) -> SyntaxValidationResult:
        self.logger.info("Syntax validation started")
        result = self.syntax_checker.validate_python_code(test_code)
        self.logger.info("Syntax validation finished: is_valid=%s", result.is_valid)
        return result
