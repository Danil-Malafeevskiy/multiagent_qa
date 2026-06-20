from qa_testgen.services.syntax_checker import SyntaxChecker


def test_valid_python_code() -> None:
    result = SyntaxChecker().validate_python_code("def test_ok():\n    assert 1 == 1\n")

    assert result.is_valid is True
    assert result.error_message is None


def test_invalid_python_code() -> None:
    result = SyntaxChecker().validate_python_code("def test_broken(:\n    pass\n")

    assert result.is_valid is False
    assert result.error_message
    assert result.line_number == 1


def test_empty_python_code_is_invalid() -> None:
    result = SyntaxChecker().validate_python_code("  \n")

    assert result.is_valid is False
    assert result.error_message == "Generated test code is empty"
