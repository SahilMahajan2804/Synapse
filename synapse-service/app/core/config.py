from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

	internal_key: SecretStr | None = Field(
		default=None,
		validation_alias=AliasChoices("SYNAPSE_INTERNAL_KEY", "internal_key"),
	)
	spacy_model: str = "en_core_web_lg"
	score_threshold: float = 0.35
	ignored_types: list[str] = Field(default_factory=lambda: ["NRP", "URL"])
	session_ttl_seconds: int = 1800
	max_sessions: int = 1000
	date_shift_min: int = 30
	date_shift_max: int = 180
	reverse_date_mode: Literal["KNOWN_ONLY", "ALL"] = "KNOWN_ONLY"
	max_text_chars: int = 200_000


@lru_cache
def get_settings() -> Settings:
	return Settings()