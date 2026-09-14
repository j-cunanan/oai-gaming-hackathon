from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="REPRO_")

    openai_api_key: SecretStr | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    model: str = "gpt-5.6-luna"
    reasoning_effort: str = "low"
    data_dir: Path = Path(".repro")
    sandbox_dir: Path | None = None
    worker_image: str = "repro-worker:local"
    worker_platform: str = "linux/amd64"
    validation_network: bool = False
    max_model_calls: int = Field(default=60, ge=1, le=300)
    max_output_tokens: int = Field(default=4000, ge=512, le=32000)
    max_seconds: int = Field(default=1800, ge=30, le=14400)
    repetitions: int = Field(default=5, ge=2, le=20)
    max_actions: int = Field(default=120, ge=1, le=500)

    @property
    def root(self) -> Path:
        return self.data_dir.resolve()
