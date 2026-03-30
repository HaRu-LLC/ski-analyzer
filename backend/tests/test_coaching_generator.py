"""CoachingGenerator のユニットテスト."""

import json

from app.services.coaching_generator import CoachingGenerator


class _FakeResponse:
    def __init__(self, output_text: str):
        self.output_text = output_text


class _FakeResponses:
    def __init__(self, outputs):
        self._outputs = list(outputs)

    def create(self, **kwargs):
        if not self._outputs:
            raise AssertionError("unexpected OpenAI responses.create call")
        return _FakeResponse(self._outputs.pop(0))


class _FakeOpenAI:
    def __init__(self, *, api_key: str, outputs):
        self.api_key = api_key
        self.responses = _FakeResponses(outputs)


class TestCoachingGenerator:
    """CoachingGenerator のテスト."""

    def test_unknown_provider_returns_default(self, monkeypatch):
        monkeypatch.setattr("app.core.settings.llm_provider", "unknown")
        generator = CoachingGenerator()

        coaching, metadata = generator.generate_with_metadata(
            {"左膝": {"flexion": {"mean": -40.0}}}
        )

        assert coaching["overall_score"] == 0
        assert metadata["fallback_reason"] == "unknown_llm_provider"

    def test_openai_without_key_returns_default(self, monkeypatch):
        monkeypatch.setattr("app.core.settings.llm_provider", "openai")
        monkeypatch.setattr("app.core.settings.openai_api_key", "")
        generator = CoachingGenerator()

        coaching, metadata = generator.generate_with_metadata(
            {"左膝": {"flexion": {"mean": -40.0}}}
        )

        assert coaching["overall_score"] == 0
        assert metadata["fallback_reason"] == "missing_openai_api_key"

    def test_openai_review_can_rewrite_output(self, monkeypatch):
        monkeypatch.setattr("app.core.settings.llm_provider", "openai")
        monkeypatch.setattr("app.core.settings.openai_api_key", "sk-test")
        monkeypatch.setattr("app.core.settings.openai_agent_model", "gpt-5.2")
        monkeypatch.setattr("app.core.settings.openai_reasoning_effort", "low")

        candidate = json.dumps(
            {
                "overall_score": 76,
                "summary": "全体の安定感がありますが、前傾が足りません。",
                "details": [
                    {
                        "joint": "膝",
                        "advice": "もう少し前に体を倒しましょう。",
                        "reason": "前傾が不足しているためです。",
                        "exercise": "壁にもたれて感覚を覚えます。",
                        "priority": "high",
                    }
                ],
            },
            ensure_ascii=False,
        )
        review = json.dumps(
            {
                "decision": "rewrite",
                "issues": ["low_confidence_claim"],
                "corrected_output": {
                    "overall_score": 76,
                    "summary": (
                        "全体の安定感があります。前傾は参考値のため、"
                        "目安として確認してください。"
                    ),
                    "details": [
                        {
                            "joint": "膝",
                            "advice": "膝の曲げを少し深くすると安定しやすくなります。",
                            "reason": "膝の使い方は今回のデータで比較しやすい指標です。",
                            "exercise": "その場でゆっくり膝を曲げ伸ばしして感覚を整えます。",
                            "priority": "high",
                        }
                    ],
                },
            },
            ensure_ascii=False,
        )

        def _fake_openai(api_key: str):
            return _FakeOpenAI(api_key=api_key, outputs=[candidate, review])

        monkeypatch.setattr("app.services.coaching_generator.OpenAI", _fake_openai)
        generator = CoachingGenerator()

        coaching, metadata = generator.generate_with_metadata(
            {"左膝": {"flexion": {"mean": -48.0, "std": 3.0}}},
            ideal_comparison=[
                {
                    "joint_name": "左膝",
                    "joint_name_ja": "左膝",
                    "user_angle": -48.0,
                    "ideal_angle": -55.0,
                    "difference": 7.0,
                    "rating": "good",
                }
            ],
        )

        assert coaching["summary"].startswith("全体の安定感があります。")
        assert metadata["provider"] == "openai"
        assert metadata["review_decision"] == "rewrite"
        assert metadata["review_issues"] == ["low_confidence_claim"]

    def test_openai_review_reject_preserves_issues(self, monkeypatch):
        monkeypatch.setattr("app.core.settings.llm_provider", "openai")
        monkeypatch.setattr("app.core.settings.openai_api_key", "sk-test")
        monkeypatch.setattr("app.core.settings.openai_agent_model", "gpt-5.2")
        monkeypatch.setattr("app.core.settings.openai_reasoning_effort", "low")

        candidate = json.dumps(
            {
                "overall_score": 60,
                "summary": "体の向きに改善余地があります。",
                "details": [
                    {
                        "joint": "肩",
                        "advice": "もっと大きくひねりましょう。",
                        "reason": "回旋が不足しています。",
                        "exercise": "上体だけをひねる練習です。",
                        "priority": "high",
                    }
                ],
            },
            ensure_ascii=False,
        )
        review = json.dumps(
            {
                "decision": "reject",
                "issues": ["unsupported_claim", "low_confidence_claim"],
                "corrected_output": {
                    "overall_score": 60,
                    "summary": "体の向きに改善余地があります。",
                    "details": [],
                },
            },
            ensure_ascii=False,
        )

        def _fake_openai(api_key: str):
            return _FakeOpenAI(api_key=api_key, outputs=[candidate, review])

        monkeypatch.setattr("app.services.coaching_generator.OpenAI", _fake_openai)
        generator = CoachingGenerator()

        coaching, metadata = generator.generate_with_metadata(
            {"左膝": {"flexion": {"mean": -48.0, "std": 3.0}}}
        )

        assert coaching["overall_score"] == 0
        assert metadata["fallback_reason"] == "openai_review_rejected"
        assert metadata["review_issues"] == ["unsupported_claim", "low_confidence_claim"]

    def test_normalize_keeps_usable_optional_fields_missing(self):
        coaching = CoachingGenerator._normalize_coaching(
            {
                "overall_score": 74,
                "summary": "全体のバランスは良好です。",
                "details": [
                    {
                        "joint": "膝",
                        "advice": "膝の曲げを少し深くしましょう。",
                        "priority": "high",
                    }
                ],
            }
        )

        assert coaching["overall_score"] == 74
        assert coaching["summary"] == "全体のバランスは良好です。"
        assert coaching["details"] == [
            {
                "joint": "膝",
                "advice": "膝の曲げを少し深くしましょう。",
                "priority": "high",
            }
        ]

    def test_local_guardrail_checks_low_confidence_per_statement(self):
        from app.services.coaching_generator import _OpenAICoachingProvider

        issues = _OpenAICoachingProvider._local_guardrail_issues(
            {
                "summary": "前傾は参考値として見てください。回旋が足りません。",
                "details": [],
            }
        )

        assert issues == ["low_confidence_axes_are_described_too_confidently"]

    def test_summarize_angles(self):
        frame_data = [
            {
                "joint_angles": [
                    {
                        "joint_name_ja": "左膝",
                        "flexion": -50.0,
                        "rotation": 1.0,
                        "abduction": -2.0,
                    }
                ]
            },
            {
                "joint_angles": [
                    {
                        "joint_name_ja": "左膝",
                        "flexion": -55.0,
                        "rotation": 2.0,
                        "abduction": -3.0,
                    }
                ]
            },
        ]

        summary = CoachingGenerator.summarize_angles(frame_data)

        assert summary["左膝"]["flexion"]["mean"] == -52.5
        assert summary["左膝"]["rotation"]["max"] == 2.0
