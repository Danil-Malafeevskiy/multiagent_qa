from enum import StrEnum


class ScenarioType(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    EDGE = "edge"
    ERROR_HANDLING = "error_handling"


class ValidationStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    NEEDS_REVISION = "needs_revision"


class TestGenerationStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_RETRY = "needs_retry"
