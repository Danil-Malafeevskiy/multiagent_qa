import ast

from qa_testgen.domain.models import SyntaxValidationResult


class SyntaxChecker:
    def validate_python_code(self, code: str) -> SyntaxValidationResult:
        if not code.strip():
            return SyntaxValidationResult(
                is_valid=False,
                error_message="Generated test code is empty",
                details="At least one Python statement is required.",
            )
        try:
            ast.parse(code)
        except SyntaxError as exc:
            return SyntaxValidationResult(
                is_valid=False,
                error_message=exc.msg,
                line_number=exc.lineno,
                details=exc.text.strip() if exc.text else None,
            )
        return SyntaxValidationResult(is_valid=True)
