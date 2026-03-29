"""AIコーチング生成サービス: Claude APIによるフォーム改善アドバイス."""

import json
import logging

import anthropic

from app.core import settings

logger = logging.getLogger(__name__)

COACHING_SYSTEM_PROMPT = """\
あなたはプロのスキーインストラクターです。
スキーシミュレータで撮影された滑走動画のAI姿勢解析結果に基づいて、
具体的で分かりやすい日本語のフォーム改善アドバイスを提供してください。

以下のルールに従ってください:
1. 良い点を先に褒める
2. 改善ポイントは優先度順に3〜5個
3. 各ポイントには「なぜ改善が必要か」「具体的な練習方法」を含める
4. 専門用語は使わず、初心者にもわかる表現を使う
5. 正面カメラ1台の制約で精度が低い指標（前傾・回旋）は断定を避ける

出力はJSON形式で:
{
  "overall_score": 75,
  "summary": "全体的な評価コメント",
  "details": [
    {
      "joint": "膝",
      "advice": "改善アドバイス",
      "reason": "なぜ改善が必要か",
      "exercise": "練習方法",
      "priority": "high"
    }
  ]
}
"""


class CoachingGenerator:
    """Claude APIを用いたAIコーチングテキスト生成."""

    def __init__(self):
        """Anthropicクライアントを初期化する."""
        self._client = None
        if settings.anthropic_api_key:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def generate(self, angle_summary: dict) -> dict:
        """解析結果からコーチングアドバイスを生成する.

        Args:
            angle_summary: 関節角度の要約データ

        Returns:
            CoachingAdviceスキーマに対応するdict
        """
        if self._client is None:
            logger.warning("Anthropic API key not set, returning default coaching")
            return self._default_coaching()

        try:
            user_message = (
                "以下のスキーフォーム解析結果に基づいてアドバイスしてください:\n\n"
                f"{json.dumps(angle_summary, ensure_ascii=False, indent=2)}"
            )

            response = self._client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=COACHING_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text
            # JSON部分を抽出
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])

            return self._default_coaching()

        except Exception as e:
            logger.error("Coaching generation failed: %s", e)
            return self._default_coaching()

    @staticmethod
    def _default_coaching() -> dict:
        """デフォルトのコーチングデータ."""
        return {
            "overall_score": 0,
            "summary": "コーチング生成に失敗しました。解析データを確認してください。",
            "details": [],
        }

    @staticmethod
    def summarize_angles(frame_data_list: list[dict]) -> dict:
        """時系列の関節角度データを要約する.

        全フレームの平均・最大・最小角度を算出する。

        Args:
            frame_data_list: AngleCalculator.calculate_video_angles() の出力

        Returns:
            関節ごとの角度統計
        """
        from collections import defaultdict

        stats: dict[str, dict[str, list]] = defaultdict(
            lambda: {"flexion": [], "rotation": [], "abduction": []}
        )

        for frame in frame_data_list:
            for angle in frame.get("joint_angles", []):
                name = angle["joint_name_ja"]
                if angle.get("flexion") is not None:
                    stats[name]["flexion"].append(angle["flexion"])
                if angle.get("rotation") is not None:
                    stats[name]["rotation"].append(angle["rotation"])
                if angle.get("abduction") is not None:
                    stats[name]["abduction"].append(angle["abduction"])

        import numpy as np

        summary = {}
        for joint, axes in stats.items():
            summary[joint] = {}
            for axis, values in axes.items():
                if values:
                    arr = np.array(values)
                    summary[joint][axis] = {
                        "mean": round(float(np.mean(arr)), 1),
                        "min": round(float(np.min(arr)), 1),
                        "max": round(float(np.max(arr)), 1),
                        "std": round(float(np.std(arr)), 1),
                    }

        return summary
