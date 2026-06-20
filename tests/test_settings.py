from pathlib import Path

from pydantic import SecretStr

from qa_testgen.config.settings import AppSettings


def test_empty_llm_base_url_is_normalized_to_none(tmp_path: Path) -> None:
    settings = AppSettings(
        llm_provider="openai",
        llm_model="fake",
        llm_base_url="  ",
        llm_temperature=0,
        llm_max_tokens=100,
        openai_api_key=SecretStr("fake"),
        max_scenario_validation_attempts=1,
        max_test_generation_attempts=1,
        artifacts_dir=tmp_path,
        log_level="INFO",
    )

    assert settings.llm_base_url is None

