"""应用配置：全部通过环境变量或 backend/.env 注入，避免把密钥写进代码。"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "AI Learn 问答服务"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'ai_learn.db').as_posix()}"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # MiMo 模型服务（OpenAI 兼容接口），地址与模型名都由环境变量提供
    mimo_base_url: str = ""
    mimo_api_key: str = ""
    mimo_model: str = ""
    llm_timeout: float = 60.0
    llm_max_history: int = 10

    # 本地演示开关：不调用真实模型，直接返回固定回答
    mock_llm: bool = False

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
