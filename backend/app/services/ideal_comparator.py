"""理想フォーム比較サービス."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# デフォルトの理想フォームデータ（中級者向けパラレルターン）
DEFAULT_IDEAL_FORM = {
    "左膝": {"flexion": -55.0, "rotation": 0.0, "abduction": -5.0},
    "右膝": {"flexion": -55.0, "rotation": 0.0, "abduction": -5.0},
    "左股関節": {"flexion": -45.0, "rotation": 0.0, "abduction": -10.0},
    "右股関節": {"flexion": -45.0, "rotation": 0.0, "abduction": -10.0},
    "脊椎下部": {"flexion": -15.0, "rotation": 0.0, "abduction": 0.0},
    "脊椎中部": {"flexion": -10.0, "rotation": 0.0, "abduction": 0.0},
    "脊椎上部": {"flexion": -5.0, "rotation": 0.0, "abduction": 0.0},
    "左肩": {"flexion": 10.0, "rotation": 0.0, "abduction": 25.0},
    "右肩": {"flexion": 10.0, "rotation": 0.0, "abduction": 25.0},
    "頭": {"flexion": -5.0, "rotation": 0.0, "abduction": 0.0},
    "左肘": {"flexion": -30.0, "rotation": 0.0, "abduction": 0.0},
    "右肘": {"flexion": -30.0, "rotation": 0.0, "abduction": 0.0},
}

# 許容誤差（度）: この範囲内なら "good"
TOLERANCE = {
    "good": 10.0,
    "needs_improvement": 20.0,
    # 20度超 → "poor"
}


class IdealComparator:
    """ユーザーのフォームと理想フォームを比較する."""

    def __init__(self, ideal_form_path: Path | None = None):
        """理想フォームデータをロードする.

        Args:
            ideal_form_path: カスタム理想フォームJSONのパス（省略時はデフォルト使用）
        """
        if ideal_form_path and ideal_form_path.exists():
            self._ideal = json.loads(ideal_form_path.read_text())
        else:
            self._ideal = DEFAULT_IDEAL_FORM

    def compare(self, angle_summary: dict) -> list[dict]:
        """角度要約データと理想フォームを比較する.

        Args:
            angle_summary: CoachingGenerator.summarize_angles() の出力

        Returns:
            IdealComparisonスキーマに対応するdictのリスト
        """
        comparisons = []

        for joint_ja, ideal_angles in self._ideal.items():
            if joint_ja not in angle_summary:
                continue

            user_stats = angle_summary[joint_ja]

            # 屈曲角度を主要比較指標とする
            if "flexion" not in user_stats:
                continue

            user_angle = user_stats["flexion"]["mean"]
            ideal_angle = ideal_angles["flexion"]
            diff = abs(user_angle - ideal_angle)

            if diff <= TOLERANCE["good"]:
                rating = "good"
            elif diff <= TOLERANCE["needs_improvement"]:
                rating = "needs_improvement"
            else:
                rating = "poor"

            comparisons.append(
                {
                    "joint_name": joint_ja,
                    "joint_name_ja": joint_ja,
                    "user_angle": user_angle,
                    "ideal_angle": ideal_angle,
                    "difference": round(diff, 1),
                    "rating": rating,
                }
            )

        # 差分が大きい順にソート
        comparisons.sort(key=lambda x: x["difference"], reverse=True)
        return comparisons
