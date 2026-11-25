"""Configuration for public YouTube Data API access."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings used by YouTube API providers."""

    model_config = SettingsConfigDict(env_prefix="YOUTUBE_", env_file=".env", extra="ignore")

    api_key: SecretStr | None = None
    max_search_results: int = Field(default=25, ge=1, le=50)
    max_upload_sample: int = Field(default=20, ge=1, le=50)


settings = Settings()
