from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    neis_api_key: str = Field(default="", alias="NEIS_API_KEY")
    frontend_origin: str = Field(default="http://localhost:3000", alias="FRONTEND_ORIGIN")
    database_path: str = Field(default="./data/app.db", alias="DATABASE_PATH")
    tournament_run_hour: int = Field(default=0, alias="TOURNAMENT_RUN_HOUR")
    tournament_run_minute: int = Field(default=10, alias="TOURNAMENT_RUN_MINUTE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        db_path = Path(self.database_path)
        if not db_path.is_absolute():
            db_path = Path(__file__).resolve().parents[1] / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path.resolve()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
