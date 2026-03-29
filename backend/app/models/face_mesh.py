"""MediaPipe Face Mesh による頭部回転補完.

正面カメラ1台では頭部の前後傾きの推定精度が低いため、
468点の顔ランドマークから3D回転を高精度に推定して補完する。
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


class FaceMeshEstimator:
    """MediaPipe Face Meshによる頭部3D回転推定.

    顔の468ランドマークから頭部の3D回転（pitch, yaw, roll）を算出し、
    HMRモデルの頭部回転推定を補完する。
    """

    def __init__(self):
        """MediaPipe Face Meshを初期化する."""
        self._face_mesh = None
        try:
            import mediapipe as mp

            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
            )
            logger.info("MediaPipe Face Mesh initialized")
        except ImportError:
            logger.warning("mediapipe not installed, face mesh disabled")

    def estimate_head_rotation(self, image: np.ndarray) -> dict | None:
        """画像から頭部の3D回転を推定する.

        Args:
            image: BGR画像 (H, W, 3)

        Returns:
            {"pitch": float, "yaw": float, "roll": float} (度)
            顔が検出されない場合は None
        """
        if self._face_mesh is None:
            return None

        import cv2

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self._face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return None

        landmarks = results.multi_face_landmarks[0]
        h, w = image.shape[:2]

        # 主要ランドマークの3D座標を取得
        # 鼻先(1), 顎(152), 左目外側(33), 右目外側(263), 左口角(61), 右口角(291)
        key_indices = [1, 152, 33, 263, 61, 291]
        points_3d = []
        points_2d = []

        for idx in key_indices:
            lm = landmarks.landmark[idx]
            points_3d.append([lm.x * w, lm.y * h, lm.z * w])
            points_2d.append([lm.x * w, lm.y * h])

        points_3d = np.array(points_3d, dtype=np.float64)
        points_2d = np.array(points_2d, dtype=np.float64)

        # solvePnP で回転ベクトルを推定
        camera_matrix = np.array([
            [w, 0, w / 2],
            [0, w, h / 2],
            [0, 0, 1],
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        success, rotation_vec, _ = cv2.solvePnP(
            points_3d, points_2d, camera_matrix, dist_coeffs
        )

        if not success:
            return None

        # 回転ベクトル → 回転行列 → Euler角
        rotation_mat, _ = cv2.Rodrigues(rotation_vec)
        angles = self._rotation_matrix_to_euler(rotation_mat)

        return {
            "pitch": round(float(np.degrees(angles[0])), 1),  # 上下
            "yaw": round(float(np.degrees(angles[1])), 1),    # 左右
            "roll": round(float(np.degrees(angles[2])), 1),   # 傾き
        }

    @staticmethod
    def _rotation_matrix_to_euler(R: np.ndarray) -> np.ndarray:
        """回転行列からEuler角 (pitch, yaw, roll) を算出する."""
        sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
        singular = sy < 1e-6

        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0

        return np.array([x, y, z])

    def close(self):
        """リソースを解放する."""
        if self._face_mesh:
            self._face_mesh.close()
