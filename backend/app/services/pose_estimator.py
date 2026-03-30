"""3Dポーズ推定サービス: SMPLベースHMR."""

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

import numpy as np

from app.core import settings
from app.core.exceptions import ModelNotLoadedError, PoseEstimationError

logger = logging.getLogger(__name__)

REQUIRED_MODEL_FILES = {
    "hmr2": "hmr2_model.pt",
    "smpl": "SMPL_NEUTRAL.pkl",
}

# SMPL 24関節の定義
SMPL_JOINT_NAMES = [
    "pelvis",
    "l_hip",
    "r_hip",
    "spine1",
    "l_knee",
    "r_knee",
    "spine2",
    "l_ankle",
    "r_ankle",
    "spine3",
    "l_foot",
    "r_foot",
    "neck",
    "l_collar",
    "r_collar",
    "head",
    "l_shoulder",
    "r_shoulder",
    "l_elbow",
    "r_elbow",
    "l_wrist",
    "r_wrist",
    "l_hand",
    "r_hand",
]

# 解析対象関節のインデックス
TARGET_JOINTS = {
    "l_knee": 4,
    "r_knee": 5,
    "l_hip": 1,
    "r_hip": 2,
    "spine1": 3,
    "spine2": 6,
    "spine3": 9,
    "l_shoulder": 16,
    "r_shoulder": 17,
    "neck": 12,
    "head": 15,
    "l_elbow": 18,
    "r_elbow": 19,
    "l_wrist": 20,
    "r_wrist": 21,
}

# 日本語名マッピング
JOINT_NAME_JA = {
    "l_knee": "左膝",
    "r_knee": "右膝",
    "l_hip": "左股関節",
    "r_hip": "右股関節",
    "spine1": "脊椎下部",
    "spine2": "脊椎中部",
    "spine3": "脊椎上部",
    "l_shoulder": "左肩",
    "r_shoulder": "右肩",
    "neck": "首",
    "head": "頭",
    "l_elbow": "左肘",
    "r_elbow": "右肘",
    "l_wrist": "左手首",
    "r_wrist": "右手首",
}


class PoseEstimator:
    """SMPLベースHMRによる3Dポーズ推定エンジン.

    シングルトンパターンでモデルを管理する。
    """

    _instance: ClassVar["PoseEstimator | None"] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, use_mock: bool | None = None):
        """モデルを初期化する.

        Args:
            use_mock: モックモード指定。Noneの場合は settings.use_mock を参照する。
        """
        self._model = None
        self._device = "cpu"
        self._use_mock = use_mock if use_mock is not None else settings.use_mock

        if self._use_mock:
            logger.info("Mock mode: skipping model load")
            return

        self._load_model()

    def _load_model(self):
        """HMRモデルをロードする."""
        try:
            import torch

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Using device: %s", self._device)
            missing_files = [
                str(settings.model_path / filename)
                for filename in REQUIRED_MODEL_FILES.values()
                if not (settings.model_path / filename).exists()
            ]
            if missing_files:
                raise ModelNotLoadedError(
                    "必要なモデルファイルが不足しています: " + ", ".join(missing_files)
                )

            # TODO: 実際のHMRモデルロード
            # from hmr2 import HMR2
            # self._model = HMR2.from_pretrained(settings.model_path / "hmr2")
            # self._model.to(self._device)
            # self._model.eval()
            raise ModelNotLoadedError(
                "USE_MOCK=false が指定されていますが、実 HMR 推論ランタイムはまだ未統合です。"
            )
        except Exception as e:
            if isinstance(e, ModelNotLoadedError):
                raise
            raise ModelNotLoadedError(f"モデルのロードに失敗: {e}") from e

    @classmethod
    def get_instance(cls) -> "PoseEstimator":
        """シングルトンインスタンスを取得する（スレッドセーフ）."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def estimate_frame(self, image_path: Path) -> dict:
        """1フレームの3Dポーズを推定する.

        Args:
            image_path: 入力画像パス

        Returns:
            {
                "joint_positions_3d": {joint_name: [x, y, z]},
                "joint_rotations": {joint_name: [rx, ry, rz]},  # axis-angle
                "smpl_params": {"betas": [...], "body_pose": [...], "global_orient": [...]}
            }
        """
        if self._use_mock:
            return self._generate_mock_data()

        try:
            raise PoseEstimationError("実 HMR 推論は未実装です。USE_MOCK=true で実行してください。")
        except Exception as e:
            if isinstance(e, PoseEstimationError):
                raise
            raise PoseEstimationError(f"ポーズ推定に失敗: {e}") from e

    def estimate_video(
        self,
        frame_paths: list[Path],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[dict]:
        """動画全フレームの3Dポーズを推定する.

        Args:
            frame_paths: フレーム画像パスのリスト
            progress_callback: 進捗コールバック (current, total) -> None

        Returns:
            フレームごとの推定結果リスト
        """
        results = []
        total = len(frame_paths)

        for i, path in enumerate(frame_paths):
            result = self.estimate_frame(path)
            results.append(result)

            if progress_callback and i % 10 == 0:
                progress_callback(i, total)

        logger.info("Estimated poses for %d frames", total)
        return results

    def _generate_mock_data(self) -> dict:
        """開発用モックデータを生成する."""
        rng = np.random.default_rng()

        positions = {}
        rotations = {}

        for name, idx in TARGET_JOINTS.items():
            positions[name] = (rng.standard_normal(3) * 0.3).tolist()
            rotations[name] = (rng.standard_normal(3) * 0.5).tolist()

        return {
            "joint_positions_3d": positions,
            "joint_rotations": rotations,
            "smpl_params": {
                "betas": (rng.standard_normal(10) * 0.1).tolist(),
                "body_pose": (rng.standard_normal(69) * 0.3).tolist(),
                "global_orient": (rng.standard_normal(3) * 0.1).tolist(),
            },
        }
