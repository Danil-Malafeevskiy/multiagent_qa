from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Конфигурация приложения, загружаемая из окружения и `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    app_name: str = "qa-testgen-prototype"
    llm_provider: str
    llm_model: str
    llm_base_url: str | None = None
    llm_temperature: float = Field(ge=0, le=2)
    llm_max_tokens: int = Field(gt=0)
    llm_request_timeout_seconds: float = Field(default=600, gt=0)
    llm_http_max_retries: int = Field(default=2, ge=0)
    openai_api_key: SecretStr
    max_scenario_validation_attempts: int = Field(ge=1)
    max_test_generation_attempts: int = Field(ge=1)
    max_llm_schema_repair_attempts: int = Field(default=1, ge=0)
    max_llm_response_parse_retries: int = Field(default=1, ge=0)
    artifacts_dir: Path
    log_level: str

    @field_validator("llm_base_url", mode="before")
    @classmethod
    def normalize_empty_base_url(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("artifacts_dir")
    @classmethod
    def create_artifacts_dir(cls, value: Path) -> Path:
        value.mkdir(parents=True, exist_ok=True)
        return value

    @property
    def openai_api_key_value(self) -> str:
        """Возвращает секрет только для передачи клиенту провайдера."""
        return self.openai_api_key.get_secret_value()


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
