"""API ルーティング定義."""

import json
import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core import settings
from app.core.exceptions import VideoValidationError
from app.schemas.analysis import AnalysisResult, StatusResponse, UploadResponse
from app.services.video_processor import VideoProcessor

logger = logging.getLogger(__name__)
router = APIRouter()

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _validate_analysis_id(analysis_id: str) -> Path:
    """analysis_id を検証し、安全なディレクトリパスを返す.

    UUID形式チェックとパストラバーサル防止を行う。

    Args:
        analysis_id: 検証対象のID文字列

    Returns:
        storage_path 配下の解析ディレクトリパス

    Raises:
        HTTPException: 不正なIDの場合
    """
    if not _UUID_RE.match(analysis_id):
        raise HTTPException(status_code=400, detail="不正な解析IDです")

    resolved = (settings.storage_path / analysis_id).resolve()
    if not resolved.is_relative_to(settings.storage_path.resolve()):
        raise HTTPException(status_code=400, detail="不正な解析IDです")

    return resolved


# インメモリの解析状況管理（本番ではRedisに移行）
_analysis_store: dict[str, dict] = {}


def _artifact_status_from_files(analysis_dir: Path) -> dict[str, bool]:
    """解析ディレクトリ上の成果物存在有無を返す."""
    return {
        "video": (analysis_dir / "overlay.mp4").exists(),
        "report": (analysis_dir / "report.pdf").exists(),
        "csv": (analysis_dir / "angles.csv").exists(),
    }


def _hydrate_result_artifacts(data: dict, analysis_dir: Path) -> dict:
    """保存済み結果に artifact 情報を補完する."""
    data["artifacts"] = _artifact_status_from_files(analysis_dir)
    return data


def run_analysis_background(
    analysis_id: str,
    video_path: Path,
    fps: float,
    video_info: dict | None = None,
) -> None:
    """バックグラウンドで解析パイプラインを実行する."""
    from app.services.analysis_pipeline import AnalysisPipeline

    def _update_status(stage: str, percent: float) -> None:
        _analysis_store[analysis_id] = {
            **_analysis_store.get(analysis_id, {}),
            "status": stage,
            "progress": percent,
        }

    try:
        pipeline = AnalysisPipeline(use_mock=settings.use_mock)
        pipeline.run(
            video_path=video_path,
            output_dir=video_path.parent,
            fps=fps,
            analysis_id=analysis_id,
            video_info=video_info,
            progress_callback=_update_status,
        )
        _update_status("completed", 100.0)
    except Exception:
        logger.exception("Analysis failed: %s", analysis_id)
        _analysis_store[analysis_id] = {
            **_analysis_store.get(analysis_id, {}),
            "status": "failed",
            "progress": 0,
            "error": "解析中にエラーが発生しました",
        }


@router.post("/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile, background_tasks: BackgroundTasks):
    """動画をアップロードして解析を開始する."""
    # 拡張子チェック
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"非対応の形式です。対応形式: {', '.join(settings.allowed_extensions)}",
        )

    # ファイルサイズチェック
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"ファイルサイズが上限（{settings.max_file_size // 1_000_000}MB）を超えています",
        )

    # 保存
    analysis_id = str(uuid.uuid4())
    save_dir = settings.storage_path / analysis_id
    save_dir.mkdir(parents=True, exist_ok=True)
    video_path = save_dir / f"original{ext}"
    video_path.write_bytes(content)

    # 動画バリデーション
    try:
        video_info = VideoProcessor.validate(video_path)
    except VideoValidationError as e:
        video_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e)) from e

    # 解析タスクをキューに投入
    _analysis_store[analysis_id] = {
        "status": "validating",
        "progress": 0,
        "video_path": str(video_path),
        "video_info": video_info,
    }

    # BackgroundTasks でパイプラインを非同期実行
    background_tasks.add_task(
        run_analysis_background,
        analysis_id=analysis_id,
        video_path=video_path,
        fps=video_info.get("fps", 30.0),
        video_info=video_info,
    )

    logger.info("Analysis started: %s", analysis_id)
    return UploadResponse(
        analysis_id=analysis_id,
        status="validating",
        message="動画を受け付けました。解析を開始します。",
    )


@router.get("/analysis/{analysis_id}/status", response_model=StatusResponse)
async def get_analysis_status(analysis_id: str):
    """解析状況を取得する."""
    analysis_dir = _validate_analysis_id(analysis_id)
    if analysis_id not in _analysis_store:
        raise HTTPException(status_code=404, detail="解析結果が見つかりません")

    store = _analysis_store[analysis_id]
    return StatusResponse(
        analysis_id=analysis_id,
        status=store["status"],
        progress=store.get("progress", 0),
        estimated_remaining_seconds=store.get("eta"),
        error_message=store.get("error"),
        artifacts=_artifact_status_from_files(analysis_dir),
    )


@router.get("/analysis/{analysis_id}/result", response_model=AnalysisResult)
async def get_analysis_result(analysis_id: str):
    """解析結果を取得する."""
    analysis_dir = _validate_analysis_id(analysis_id)
    result_path = analysis_dir / "result.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="解析結果が見つかりません")

    data = json.loads(result_path.read_text())
    data = _hydrate_result_artifacts(data, analysis_dir)
    return AnalysisResult(**data)


@router.get("/analysis/{analysis_id}/frames/{frame_index}")
async def get_frame_data(analysis_id: str, frame_index: int):
    """特定フレームの解析データを取得する."""
    analysis_dir = _validate_analysis_id(analysis_id)
    result_path = analysis_dir / "result.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="解析結果が見つかりません")

    data = json.loads(result_path.read_text())
    frames = data.get("frames", [])
    if frame_index < 0 or frame_index >= len(frames):
        raise HTTPException(status_code=404, detail="フレームが見つかりません")

    return frames[frame_index]


@router.get("/download/{analysis_id}/video")
async def download_overlay_video(analysis_id: str):
    """スケルトン重畳動画をダウンロードする."""
    analysis_dir = _validate_analysis_id(analysis_id)
    video_path = analysis_dir / "overlay.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="動画が見つかりません")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"ski_analysis_{analysis_id[:8]}.mp4",
    )


@router.get("/download/{analysis_id}/report")
async def download_report(analysis_id: str):
    """PDFレポートをダウンロードする."""
    analysis_dir = _validate_analysis_id(analysis_id)
    report_path = analysis_dir / "report.pdf"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="レポートが見つかりません")

    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"ski_report_{analysis_id[:8]}.pdf",
    )


@router.get("/download/{analysis_id}/csv")
async def download_csv(analysis_id: str):
    """CSV数値データをダウンロードする."""
    analysis_dir = _validate_analysis_id(analysis_id)
    csv_path = analysis_dir / "angles.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSVが見つかりません")

    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=f"ski_angles_{analysis_id[:8]}.csv",
    )
