"""スケルトン重畳動画レンダリングサービス."""

import logging
import subprocess
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# 描画色 (BGR)
JOINT_COLOR = (0, 255, 136)  # #00ff88
BONE_COLOR = (0, 200, 100)
JOINT_RADIUS = 5
BONE_THICKNESS = 2

# ボーン接続定義
BONE_CONNECTIONS = [
    ("l_hip", "l_knee"),
    ("r_hip", "r_knee"),
    ("l_hip", "r_hip"),
    ("l_shoulder", "l_elbow"),
    ("l_elbow", "l_wrist"),
    ("r_shoulder", "r_elbow"),
    ("r_elbow", "r_wrist"),
    ("l_shoulder", "r_shoulder"),
    ("l_shoulder", "l_hip"),
    ("r_shoulder", "r_hip"),
    ("neck", "head"),
    ("l_shoulder", "neck"),
    ("r_shoulder", "neck"),
    ("spine1", "spine2"),
    ("spine2", "spine3"),
    ("spine3", "neck"),
    ("l_hip", "spine1"),
    ("r_hip", "spine1"),
]


class OverlayRenderer:
    """スケルトンを元動画に重畳してMP4を生成する."""

    @staticmethod
    def render(
        video_path: Path,
        frame_results: list[dict],
        output_path: Path,
    ) -> Path:
        """スケルトン重畳動画を生成する.

        Args:
            video_path: 元動画パス
            frame_results: フレームごとのポーズ推定結果
            output_path: 出力MP4パス

        Returns:
            生成された動画パス
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"動画を開けません: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 一時ファイルに書き出し（後でFFmpegで最終エンコード）
        tmp_path = output_path.with_suffix(".tmp.mp4")
        encoded_path = output_path.with_suffix(".encoded.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(tmp_path), fourcc, fps, (width, height))

        frame_idx = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx < len(frame_results):
                    frame = OverlayRenderer._draw_skeleton(
                        frame, frame_results[frame_idx], width, height
                    )

                writer.write(frame)
                frame_idx += 1
        finally:
            cap.release()
            writer.release()

        # FFmpegで再エンコード（ブラウザ互換H.264）
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(tmp_path),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-pix_fmt",
                    "yuv420p",
                    str(encoded_path),
                ],
                capture_output=True,
                check=True,
            )
            encoded_path.replace(output_path)
        except Exception:
            output_path.unlink(missing_ok=True)
            encoded_path.unlink(missing_ok=True)
            raise
        finally:
            tmp_path.unlink(missing_ok=True)
            encoded_path.unlink(missing_ok=True)

        logger.info("Overlay video rendered: %s (%d frames)", output_path, frame_idx)
        return output_path

    @staticmethod
    def _draw_skeleton(
        frame: np.ndarray,
        pose_data: dict,
        width: int,
        height: int,
    ) -> np.ndarray:
        """1フレームにスケルトンを描画する."""
        positions = pose_data.get("joint_positions_3d", {})

        def to_pixel(pos: list[float]) -> tuple[int, int] | None:
            """正規化座標 [-1, 1] をピクセル座標に変換."""
            if len(pos) < 2:
                return None
            px = int((pos[0] + 1) * width * 0.5)
            py = int((1 - pos[1]) * height * 0.5)
            return (px, py)

        # ボーン描画
        for j1, j2 in BONE_CONNECTIONS:
            if j1 in positions and j2 in positions:
                p1 = to_pixel(positions[j1])
                p2 = to_pixel(positions[j2])
                if p1 and p2:
                    cv2.line(frame, p1, p2, BONE_COLOR, BONE_THICKNESS, cv2.LINE_AA)

        # 関節ポイント描画
        for name, pos in positions.items():
            pt = to_pixel(pos)
            if pt:
                cv2.circle(frame, pt, JOINT_RADIUS, JOINT_COLOR, -1, cv2.LINE_AA)

        return frame
