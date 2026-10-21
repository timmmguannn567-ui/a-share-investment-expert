from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    app_name: str = "股市专家 · A股辅助决策系统"
    app_env: str = "development"
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'data' / 'stock_expert.db').as_posix()}"
    data_provider: str = "mock"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://timmmguannn567-ui.github.io"
    strategy_version: str = "prd-2.0.0"

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        value = self.cors_origins.strip()
        if value.startswith("["):
            return [str(item) for item in json.loads(value)]
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

