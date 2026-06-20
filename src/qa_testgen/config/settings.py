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
    llm_temperature: float = Field(ge=0, le=2)
    llm_max_tokens: int = Field(gt=0)
    openai_api_key: SecretStr
    max_scenario_validation_attempts: int = Field(ge=1)
    max_test_generation_attempts: int = Field(ge=1)
    artifacts_dir: Path
    log_level: str

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
