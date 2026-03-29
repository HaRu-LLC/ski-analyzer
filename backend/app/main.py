"""FastAPI アプリケーションエントリポイント."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理."""
    # 起動時
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    logger.info("Storage path: %s", settings.storage_path)
    logger.info("Mock mode: %s", settings.use_mock)

    if not settings.use_mock:
        # HMRモデルのプリロード（GPU warmup）
        from app.services.pose_estimator import PoseEstimator

        PoseEstimator.get_instance()
        logger.info("Pose estimation model loaded")

    yield

    # 終了時
    logger.info("Shutting down")


app = FastAPI(
    title="Ski Analyzer API",
    description="スキーシミュレータ動画解析API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)
