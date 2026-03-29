"""関節角度算出サービス: axis-angle → Euler角変換."""

import logging

import numpy as np
from scipy.spatial.transform import Rotation

from app.services.pose_estimator import JOINT_NAME_JA, TARGET_JOINTS

logger = logging.getLogger(__name__)

# 正面カメラ1台での精度レベル
CONFIDENCE_MAP = {
    "l_knee": {"flexion": "medium", "rotation": "low", "abduction": "medium"},
    "r_knee": {"flexion": "medium", "rotation": "low", "abduction": "medium"},
    "l_hip": {"flexion": "medium", "rotation": "low", "abduction": "medium"},
    "r_hip": {"flexion": "medium", "rotation": "low", "abduction": "medium"},
    "spine1": {"flexion": "low", "rotation": "low", "abduction": "low"},
    "spine2": {"flexion": "low", "rotation": "low", "abduction": "low"},
    "spine3": {"flexion": "low", "rotation": "low", "abduction": "low"},
    "l_shoulder": {"flexion": "medium", "rotation": "low", "abduction": "high"},
    "r_shoulder": {"flexion": "medium", "rotation": "low", "abduction": "high"},
    "neck": {"flexion": "low", "rotation": "medium", "abduction": "high"},
    "head": {"flexion": "low", "rotation": "medium", "abduction": "high"},
    "l_elbow": {"flexion": "medium", "rotation": "low", "abduction": "low"},
    "r_elbow": {"flexion": "medium", "rotation": "low", "abduction": "low"},
    "l_wrist": {"flexion": "low", "rotation": "low", "abduction": "low"},
    "r_wrist": {"flexion": "low", "rotation": "low", "abduction": "low"},
}


class AngleCalculator:
    """axis-angleからEuler角への変換と関節角度の算出."""

    @staticmethod
    def axis_angle_to_euler(axis_angle: list[float]) -> dict[str, float]:
        """axis-angle表現をEuler角（度）に変換する.

        Args:
            axis_angle: [rx, ry, rz] axis-angle回転ベクトル

        Returns:
            {"flexion": float, "rotation": float, "abduction": float} (度)
        """
        rotvec = np.array(axis_angle)
        rot = Rotation.from_rotvec(rotvec)
        # XYZ Euler角: X=屈曲/伸展, Y=内旋/外旋, Z=外転/内転
        euler = rot.as_euler("XYZ", degrees=True)

        return {
            "flexion": round(float(euler[0]), 1),
            "rotation": round(float(euler[1]), 1),
            "abduction": round(float(euler[2]), 1),
        }

    @classmethod
    def calculate_frame_angles(cls, pose_data: dict) -> list[dict]:
        """1フレームの全関節角度を算出する.

        Args:
            pose_data: PoseEstimator.estimate_frame() の出力

        Returns:
            JointAngleスキーマに対応するdictのリスト
        """
        rotations = pose_data.get("joint_rotations", {})
        angles = []

        for joint_name in TARGET_JOINTS:
            if joint_name not in rotations:
                continue

            euler = cls.axis_angle_to_euler(rotations[joint_name])
            confidence = CONFIDENCE_MAP.get(joint_name, {})

            # 最も高い精度レベルを代表値とする
            conf_values = list(confidence.values())
            overall_confidence = "high" if "high" in conf_values else (
                "medium" if "medium" in conf_values else "low"
            )

            angles.append({
                "joint_name": joint_name,
                "joint_name_ja": JOINT_NAME_JA.get(joint_name, joint_name),
                "flexion": euler["flexion"],
                "rotation": euler["rotation"],
                "abduction": euler["abduction"],
                "confidence": overall_confidence,
            })

        return angles

    @classmethod
    def calculate_video_angles(
        cls, pose_results: list[dict], fps: float
    ) -> list[dict]:
        """動画全体の関節角度時系列データを算出する.

        Args:
            pose_results: フレームごとのポーズ推定結果リスト
            fps: 動画のフレームレート

        Returns:
            FrameDataスキーマに対応するdictのリスト
        """
        frame_data_list = []

        for i, pose in enumerate(pose_results):
            angles = cls.calculate_frame_angles(pose)
            frame_data_list.append({
                "frame_index": i,
                "timestamp_ms": round(i / fps * 1000, 1),
                "joint_positions_3d": pose.get("joint_positions_3d", {}),
                "joint_rotations": pose.get("joint_rotations", {}),
                "joint_angles": angles,
            })

        logger.info("Calculated angles for %d frames", len(frame_data_list))
        return frame_data_list
