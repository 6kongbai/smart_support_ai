from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    DASHSCOPE_API_KEY: str
    DASHSCOPE_API_BASE: str
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str

    DEEPSEEK_MODEL: str
    QWEN_MODEL: str
    OPENAI_MODEL: str

    LANGSMITH_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
