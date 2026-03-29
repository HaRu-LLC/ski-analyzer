"""SMPLモデルラッパー.

SMPLパラメータ（β, θ）から3Dメッシュ・関節位置を生成する。
"""

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# SMPL関節インデックス定義
JOINT_NAMES = [
    "pelvis", "l_hip", "r_hip", "spine1", "l_knee", "r_knee",
    "spine2", "l_ankle", "r_ankle", "spine3", "l_foot", "r_foot",
    "neck", "l_collar", "r_collar", "head", "l_shoulder", "r_shoulder",
    "l_elbow", "r_elbow", "l_wrist", "r_wrist", "l_hand", "r_hand",
]

NUM_JOINTS = 24
NUM_BETAS = 10
NUM_POSE_PARAMS = NUM_JOINTS * 3  # axis-angle per joint


class SMPLWrapper:
    """SMPLモデルのラッパークラス.

    SMPLXライブラリをラップし、パラメータからの3D関節位置・
    メッシュ頂点の生成を提供する。

    Usage:
        smpl = SMPLWrapper(model_path="/data/models/smpl")
        joints, vertices = smpl.forward(betas, body_pose, global_orient)
    """

    def __init__(self, model_path: Path | None = None, gender: str = "neutral"):
        """SMPLモデルをロードする.

        Args:
            model_path: SMPLモデルディレクトリ
            gender: "neutral" / "male" / "female"
        """
        self._model = None
        self._gender = gender

        if model_path and model_path.exists():
            self._load(model_path)

    def _load(self, model_path: Path):
        """モデルファイルをロードする."""
        try:
            import smplx
            import torch

            self._model = smplx.create(
                str(model_path),
                model_type="smpl",
                gender=self._gender,
                batch_size=1,
            )
            logger.info("SMPL model loaded: gender=%s", self._gender)
        except Exception as e:
            logger.warning("SMPL model load failed: %s", e)

    def forward(
        self,
        betas: np.ndarray,
        body_pose: np.ndarray,
        global_orient: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """SMPLフォワードパス.

        Args:
            betas: 体型パラメータ (10,)
            body_pose: 関節回転 axis-angle (69,) = 23joints * 3
            global_orient: グローバル回転 (3,)

        Returns:
            (joints, vertices)
            - joints: 関節3D位置 (24, 3)
            - vertices: メッシュ頂点 (6890, 3)
        """
        if self._model is None:
            # モデル未ロード時はダミーデータ
            return np.zeros((NUM_JOINTS, 3)), np.zeros((6890, 3))

        import torch

        output = self._model(
            betas=torch.tensor(betas, dtype=torch.float32).unsqueeze(0),
            body_pose=torch.tensor(body_pose, dtype=torch.float32).unsqueeze(0),
            global_orient=torch.tensor(global_orient, dtype=torch.float32).unsqueeze(0),
        )

        joints = output.joints[0].detach().cpu().numpy()[:NUM_JOINTS]
        vertices = output.vertices[0].detach().cpu().numpy()

        return joints, vertices

    @staticmethod
    def joint_index(name: str) -> int:
        """関節名からインデックスを取得する."""
        return JOINT_NAMES.index(name)

    @staticmethod
    def joint_name(index: int) -> str:
        """インデックスから関節名を取得する."""
        return JOINT_NAMES[index]
