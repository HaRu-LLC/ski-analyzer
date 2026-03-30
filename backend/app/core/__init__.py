"""アプリケーション設定."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """環境変数ベースの設定."""

    # API
    api_prefix: str = "/api"

    # ストレージ
    storage_path: Path = Path("/data/uploads")
    model_path: Path = Path("/data/models")

    # 動画制約
    max_video_duration: int = 60  # 秒
    max_file_size: int = 524_288_000  # 500MB
    allowed_extensions: set[str] = {".mp4", ".mov", ".webm"}
    min_resolution: int = 1080
    min_fps: int = 30

    # 自動削除
    auto_delete_hours: int = 24

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"

    # AI
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openai_agent_model: str = "gpt-5.2"
    openai_reasoning_effort: str = "low"

    # 開発
    use_mock: bool = True
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
