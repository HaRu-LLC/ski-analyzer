"""動画処理サービス: バリデーションとフレーム抽出."""

import json
import logging
import subprocess
from pathlib import Path

from app.core import settings
from app.core.exceptions import VideoValidationError

logger = logging.getLogger(__name__)


class VideoProcessor:
    """FFmpegベースの動画処理."""

    @staticmethod
    def validate(video_path: Path) -> dict:
        """動画ファイルのバリデーション.

        Args:
            video_path: 動画ファイルパス

        Returns:
            動画メタデータ (fps, duration, width, height)

        Raises:
            VideoValidationError: バリデーション失敗時
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_streams",
                    "-show_format",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            probe = json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            raise VideoValidationError(f"動画の読み取りに失敗しました: {e}") from e

        # ビデオストリームを検索
        video_stream = None
        for stream in probe.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if video_stream is None:
            raise VideoValidationError("動画ストリームが見つかりません")

        # メタデータ抽出
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        fps_parts = video_stream.get("r_frame_rate", "0/1").split("/")
        fps = int(fps_parts[0]) / max(int(fps_parts[1]), 1)
        duration = float(probe.get("format", {}).get("duration", 0))
        total_frames = int(video_stream.get("nb_frames", fps * duration))

        # バリデーション
        errors = []
        if min(width, height) < settings.min_resolution:
            errors.append(
                f"解像度が不足しています（{width}x{height}）。"
                f"最低{settings.min_resolution}p以上が必要です。"
            )
        if fps < settings.min_fps:
            errors.append(
                f"フレームレートが不足しています（{fps:.0f}fps）。"
                f"最低{settings.min_fps}fps以上が必要です。"
            )
        if duration > settings.max_video_duration:
            errors.append(
                f"動画が長すぎます（{duration:.1f}秒）。"
                f"最大{settings.max_video_duration}秒以内にしてください。"
            )

        if errors:
            raise VideoValidationError(" / ".join(errors))

        return {
            "width": width,
            "height": height,
            "fps": round(fps, 2),
            "duration": round(duration, 2),
            "total_frames": total_frames,
        }

    @staticmethod
    def extract_frames(video_path: Path, output_dir: Path) -> list[Path]:
        """動画から全フレームをJPEG画像として抽出する.

        Args:
            video_path: 入力動画パス
            output_dir: 出力ディレクトリ

        Returns:
            抽出されたフレーム画像パスのリスト
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_pattern = str(output_dir / "frame_%06d.jpg")

        subprocess.run(
            [
                "ffmpeg",
                "-i", str(video_path),
                "-q:v", "2",  # 高品質JPEG
                output_pattern,
            ],
            capture_output=True,
            timeout=300,
            check=True,
        )

        frames = sorted(output_dir.glob("frame_*.jpg"))
        logger.info("Extracted %d frames from %s", len(frames), video_path.name)
        return frames
