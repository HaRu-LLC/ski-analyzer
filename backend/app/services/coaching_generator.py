"""AIコーチング生成サービス."""

import json
import logging
import re
from typing import Any, Literal

import anthropic
import numpy as np
from pydantic import BaseModel, Field

from app.core import settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - openai依存が未導入でもAnthropic経路は動かす
    OpenAI = None

logger = logging.getLogger(__name__)

DEFAULT_COACHING = {
    "overall_score": 0,
    "summary": "コーチング生成に失敗しました。解析データを確認してください。",
    "details": [],
}

LOW_CONFIDENCE_TERMS = ("前傾", "回旋", "ひねり", "ねじれ")
SOFTENING_TERMS = ("参考", "断定", "可能性", "傾向", "かもしれません", "目安")
STATEMENT_SPLIT_RE = re.compile(r"[。！？\n]+")

COACHING_SYSTEM_PROMPT = """\
あなたはプロのスキーインストラクターです。
与えられた解析データだけを根拠に、具体的で分かりやすい日本語のフォーム改善アドバイスを返してください。

必須ルール:
- 根拠にない事実を作らない
- 良い点を短く述べてから改善点を示す
- 改善ポイントは優先度順に最大5件
- 各ポイントに reason と exercise を必ず含める
- 専門用語を避け、初心者にもわかる表現にする
- 正面カメラ1台で精度が低い前傾・回旋は断定しない
- 出力はスキーマに厳密に従う
"""

REVIEW_SYSTEM_PROMPT = """\
あなたはスキーコーチング出力のレビュワーです。
候補の coaching が入力データに整合しているかを厳格に確認してください。

判定ルール:
- unsupported claim を含む場合は approved にしない
- 前傾・回旋のような低信頼項目を断定していたら approved にしない
- 部位名や左右を取り違えていたら approved にしない
- 問題が軽微で修正可能なら decision を rewrite にし、corrected_output を完成形で返す
- 修正不能なら decision を reject にする
- 出力はスキーマに厳密に従う
"""


class CoachingDetail(BaseModel):
    """単一のコーチング詳細."""

    joint: str
    advice: str
    reason: str
    exercise: str
    priority: Literal["high", "medium", "low"]


class CoachingOutput(BaseModel):
    """コーチング出力."""

    overall_score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1)
    details: list[CoachingDetail] = Field(default_factory=list, max_length=5)


class CoachingReviewOutput(BaseModel):
    """レビュー結果."""

    decision: Literal["approved", "rewrite", "reject"]
    issues: list[str] = Field(default_factory=list)
    corrected_output: CoachingOutput


class _BaseCoachingProvider:
    """プロバイダ共通処理."""

    provider_name = "default"

    def _default_result(self, fallback_reason: str) -> tuple[dict[str, Any], dict[str, Any]]:
        return CoachingGenerator._default_coaching(), {
            "provider": self.provider_name,
            "fallback_reason": fallback_reason,
            "review_decision": "reject",
            "review_issues": [fallback_reason],
        }

    def _coaching_payload(
        self,
        angle_summary: dict,
        ideal_comparison: list[dict] | None,
    ) -> dict[str, Any]:
        return {
            "angle_summary": angle_summary,
            "ideal_comparison_top": (ideal_comparison or [])[:5],
            "camera_limitations": {
                "high_confidence": "左右方向の位置・回転",
                "medium_confidence": "屈曲角度",
                "low_confidence": "前傾・回旋は参考値扱いで断定しない",
            },
        }


class _AnthropicCoachingProvider(_BaseCoachingProvider):
    """Anthropicベースの既存経路."""

    provider_name = "anthropic"

    def __init__(self) -> None:
        self._client = None
        if settings.anthropic_api_key:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def generate(
        self, angle_summary: dict, ideal_comparison: list[dict] | None = None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if self._client is None:
            logger.warning("Anthropic API key not set, returning default coaching")
            return self._default_result("missing_anthropic_api_key")

        try:
            payload = self._coaching_payload(angle_summary, ideal_comparison)
            response = self._client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=COACHING_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": "以下の解析結果から coaching を JSON で返してください:\n\n"
                        + json.dumps(payload, ensure_ascii=False, indent=2),
                    }
                ],
            )

            text = response.content[0].text
            parsed = CoachingGenerator._parse_json_object(text)
            coaching = CoachingGenerator._normalize_coaching(parsed)
            return coaching, {
                "provider": self.provider_name,
                "model": "claude-sonnet-4-20250514",
                "review_decision": "approved",
                "review_issues": [],
            }
        except Exception as exc:
            logger.error("Anthropic coaching generation failed: %s", exc)
            return self._default_result("anthropic_generation_failed")


class _OpenAICoachingProvider(_BaseCoachingProvider):
    """OpenAI structured output + review 経路."""

    provider_name = "openai"

    def __init__(self) -> None:
        self._client = None
        if settings.openai_api_key and OpenAI is not None:
            self._client = OpenAI(api_key=settings.openai_api_key)

    def generate(
        self, angle_summary: dict, ideal_comparison: list[dict] | None = None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not set, returning default coaching")
            return self._default_result("missing_openai_api_key")
        if OpenAI is None or self._client is None:
            logger.warning("OpenAI SDK not available, returning default coaching")
            return self._default_result("openai_sdk_unavailable")

        payload = self._coaching_payload(angle_summary, ideal_comparison)

        try:
            candidate = self._request_structured_output(
                schema=CoachingOutput,
                instructions=COACHING_SYSTEM_PROMPT,
                payload=payload,
            )
            review = self._request_structured_output(
                schema=CoachingReviewOutput,
                instructions=REVIEW_SYSTEM_PROMPT,
                payload={"input": payload, "candidate_output": candidate.model_dump()},
            )

            review_decision = review.decision
            review_issues = review.issues
            final_output = candidate

            if review.decision == "rewrite":
                final_output = review.corrected_output
            elif review.decision == "reject":
                return CoachingGenerator._default_coaching(), {
                    "provider": self.provider_name,
                    "model": settings.openai_agent_model,
                    "review_decision": "reject",
                    "review_issues": review_issues,
                    "fallback_reason": "openai_review_rejected",
                }

            final_coaching = CoachingGenerator._normalize_coaching(final_output.model_dump())
            local_issues = self._local_guardrail_issues(final_coaching)
            if local_issues:
                return CoachingGenerator._default_coaching(), {
                    "provider": self.provider_name,
                    "model": settings.openai_agent_model,
                    "review_decision": "reject",
                    "review_issues": review_issues + local_issues,
                    "fallback_reason": "local_guardrail_failed",
                }

            return final_coaching, {
                "provider": self.provider_name,
                "model": settings.openai_agent_model,
                "review_decision": review_decision,
                "review_issues": review_issues,
            }
        except Exception as exc:
            logger.error("OpenAI coaching generation failed: %s", exc)
            return self._default_result("openai_generation_failed")

    def _request_structured_output(
        self,
        schema: type[BaseModel],
        instructions: str,
        payload: dict[str, Any],
    ) -> BaseModel:
        reasoning = {"effort": settings.openai_reasoning_effort}
        response = self._client.responses.create(
            model=settings.openai_agent_model,
            instructions=instructions,
            input=json.dumps(payload, ensure_ascii=False, indent=2),
            reasoning=reasoning,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": True,
                }
            },
        )
        output_text = getattr(response, "output_text", "") or ""
        if not output_text:
            raise ValueError("OpenAI response did not contain output_text")
        return schema.model_validate_json(output_text)

    @staticmethod
    def _local_guardrail_issues(coaching: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        texts = [coaching.get("summary", "")]
        texts.extend(
            " ".join(
                [
                    detail.get("joint", ""),
                    detail.get("advice", ""),
                    detail.get("reason", ""),
                    detail.get("exercise", ""),
                ]
            )
            for detail in coaching.get("details", [])
        )
        for text in texts:
            if not isinstance(text, str):
                continue
            statements = [
                segment.strip()
                for segment in STATEMENT_SPLIT_RE.split(text)
                if segment.strip()
            ]
            for statement in statements:
                if any(term in statement for term in LOW_CONFIDENCE_TERMS) and not any(
                    softener in statement for softener in SOFTENING_TERMS
                ):
                    issues.append("low_confidence_axes_are_described_too_confidently")
                    return issues
        return issues


class CoachingGenerator:
    """AIコーチングテキスト生成 facade."""

    def __init__(self):
        """設定に応じたプロバイダを選択する."""
        self._provider_name = settings.llm_provider.lower().strip()
        self._provider = self._create_provider()

    def _create_provider(self) -> _BaseCoachingProvider:
        if self._provider_name == "openai":
            return _OpenAICoachingProvider()
        if self._provider_name == "anthropic":
            return _AnthropicCoachingProvider()

        logger.warning("Unknown llm_provider '%s', using default coaching", self._provider_name)
        return _BaseCoachingProvider()

    def generate(self, angle_summary: dict, ideal_comparison: list[dict] | None = None) -> dict:
        """解析結果からコーチングアドバイスを生成する."""
        coaching, _ = self.generate_with_metadata(angle_summary, ideal_comparison=ideal_comparison)
        return coaching

    def generate_with_metadata(
        self, angle_summary: dict, ideal_comparison: list[dict] | None = None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """解析結果からコーチングと内部メタデータを生成する."""
        if (
            isinstance(self._provider, _BaseCoachingProvider)
            and self._provider.provider_name == "default"
        ):
            return self._provider._default_result("unknown_llm_provider")
        coaching, metadata = self._provider.generate(
            angle_summary,
            ideal_comparison=ideal_comparison,
        )
        return self._normalize_coaching(coaching), metadata

    @staticmethod
    def _default_coaching() -> dict:
        """デフォルトのコーチングデータ."""
        return DEFAULT_COACHING.copy()

    @staticmethod
    def _parse_json_object(text: str) -> dict[str, Any]:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start < 0 or end <= start:
            raise ValueError("JSON object not found in model output")
        return json.loads(text[start:end])

    @staticmethod
    def _normalize_coaching(coaching: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(coaching, dict):
            logger.warning(
                "Invalid coaching payload type returned by provider; using default coaching"
            )
            return CoachingGenerator._default_coaching()

        summary = coaching.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            summary = DEFAULT_COACHING["summary"]

        score = coaching.get("overall_score", DEFAULT_COACHING["overall_score"])
        if not isinstance(score, int):
            try:
                score = int(score)
            except (TypeError, ValueError):
                score = DEFAULT_COACHING["overall_score"]
        score = max(0, min(100, score))

        normalized_details: list[dict[str, Any]] = []
        for detail in coaching.get("details", []):
            if not isinstance(detail, dict):
                continue

            joint = detail.get("joint")
            advice = detail.get("advice")
            if not isinstance(joint, str) or not joint.strip():
                continue
            if not isinstance(advice, str) or not advice.strip():
                continue

            priority = detail.get("priority")
            if priority not in {"high", "medium", "low"}:
                priority = "medium"

            normalized_detail: dict[str, Any] = {
                "joint": joint.strip(),
                "advice": advice.strip(),
                "priority": priority,
            }

            reason = detail.get("reason")
            if isinstance(reason, str) and reason.strip():
                normalized_detail["reason"] = reason.strip()

            exercise = detail.get("exercise")
            if isinstance(exercise, str) and exercise.strip():
                normalized_detail["exercise"] = exercise.strip()

            normalized_details.append(normalized_detail)

        return {
            "overall_score": score,
            "summary": summary.strip(),
            "details": normalized_details[:5],
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
