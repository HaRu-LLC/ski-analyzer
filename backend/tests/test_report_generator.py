"""ReportGenerator のテスト (TDD: テスト先行)."""

import pytest

from app.services.report_generator import ReportGenerator


@pytest.fixture()
def sample_analysis_result() -> dict:
    """テスト用の解析結果データ."""
    return {
        "analysis_id": "test-123",
        "video_info": {
            "duration": 10.0,
            "fps": 30.0,
            "width": 1920,
            "height": 1080,
        },
        "total_frames": 300,
        "frames": [
            {
                "frame_index": i,
                "timestamp_ms": round(i / 30.0 * 1000, 1),
                "joint_positions_3d": {
                    "l_knee": [0.1, -0.5, 0.0],
                    "r_knee": [0.1, -0.5, 0.0],
                    "l_hip": [0.0, -0.2, 0.0],
                    "r_hip": [0.0, -0.2, 0.0],
                    "l_shoulder": [-0.2, 0.3, 0.0],
                    "r_shoulder": [0.2, 0.3, 0.0],
                },
                "joint_rotations": {
                    "l_knee": [0.5 + i * 0.01, 0.0, 0.0],
                    "r_knee": [0.5 + i * 0.01, 0.0, 0.0],
                },
                "joint_angles": [
                    {
                        "joint_name": "l_knee",
                        "joint_name_ja": "左膝",
                        "flexion": -55.0 + i * 0.1,
                        "rotation": 0.0,
                        "abduction": -5.0,
                        "confidence": "medium",
                    },
                    {
                        "joint_name": "r_knee",
                        "joint_name_ja": "右膝",
                        "flexion": -55.0 + i * 0.1,
                        "rotation": 0.0,
                        "abduction": -5.0,
                        "confidence": "medium",
                    },
                    {
                        "joint_name": "l_hip",
                        "joint_name_ja": "左股関節",
                        "flexion": -45.0,
                        "rotation": 0.0,
                        "abduction": -10.0,
                        "confidence": "medium",
                    },
                    {
                        "joint_name": "r_hip",
                        "joint_name_ja": "右股関節",
                        "flexion": -45.0,
                        "rotation": 0.0,
                        "abduction": -10.0,
                        "confidence": "medium",
                    },
                    {
                        "joint_name": "l_shoulder",
                        "joint_name_ja": "左肩",
                        "flexion": 10.0,
                        "rotation": 0.0,
                        "abduction": 25.0,
                        "confidence": "high",
                    },
                    {
                        "joint_name": "r_shoulder",
                        "joint_name_ja": "右肩",
                        "flexion": 10.0,
                        "rotation": 0.0,
                        "abduction": 25.0,
                        "confidence": "high",
                    },
                ],
            }
            for i in range(10)  # 簡略化: 10フレーム
        ],
        "coaching": {
            "overall_score": 75,
            "summary": (
                "全体的にバランスの取れたフォームです。"
                "膝の屈曲をもう少し深くするとさらに安定します。"
            ),
            "details": [
                {
                    "joint": "膝",
                    "advice": "ターン時に膝をもう少し曲げましょう。",
                    "priority": "high",
                },
                {
                    "joint": "肩",
                    "advice": "肩のリラックスを意識しましょう。",
                    "priority": "medium",
                },
            ],
        },
        "ideal_comparison": [
            {
                "joint_name": "左膝",
                "joint_name_ja": "左膝",
                "user_angle": -50.0,
                "ideal_angle": -55.0,
                "difference": 5.0,
                "rating": "good",
            },
            {
                "joint_name": "右膝",
                "joint_name_ja": "右膝",
                "user_angle": -40.0,
                "ideal_angle": -55.0,
                "difference": 15.0,
                "rating": "needs_improvement",
            },
        ],
    }


class TestReportGenerator:
    """ReportGenerator の TDD テスト."""

    def test_generate_creates_pdf_file(self, tmp_path, sample_analysis_result):
        """PDFファイルが生成されること."""
        output_path = tmp_path / "report.pdf"
        result = ReportGenerator.generate(sample_analysis_result, output_path)
        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_generated_pdf_is_valid(self, tmp_path, sample_analysis_result):
        """生成されたファイルが有効なPDFであること (%PDF- ヘッダ確認)."""
        output_path = tmp_path / "report.pdf"
        ReportGenerator.generate(sample_analysis_result, output_path)
        with open(output_path, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"

    def test_pdf_has_multiple_pages(self, tmp_path, sample_analysis_result):
        """PDFが複数ページを持つこと."""
        from PyPDF2 import PdfReader

        output_path = tmp_path / "report.pdf"
        ReportGenerator.generate(sample_analysis_result, output_path)
        reader = PdfReader(str(output_path))
        assert len(reader.pages) >= 3  # 表紙 + 角度 + コーチング で最低3ページ

    def test_pdf_contains_japanese_text(self, tmp_path, sample_analysis_result):
        """PDFに日本語テキストが含まれること."""
        from PyPDF2 import PdfReader

        output_path = tmp_path / "report.pdf"
        ReportGenerator.generate(sample_analysis_result, output_path)
        reader = PdfReader(str(output_path))
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text() or ""
        # 表紙に「解析レポート」が含まれるはず
        assert "解析" in all_text or "レポート" in all_text

    def test_pdf_contains_score(self, tmp_path, sample_analysis_result):
        """PDFに総合スコアが含まれること."""
        from PyPDF2 import PdfReader

        output_path = tmp_path / "report.pdf"
        ReportGenerator.generate(sample_analysis_result, output_path)
        reader = PdfReader(str(output_path))
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text() or ""
        assert "75" in all_text  # overall_score

    def test_pdf_contains_coaching_advice(self, tmp_path, sample_analysis_result):
        """PDFにコーチングアドバイスが含まれること."""
        from PyPDF2 import PdfReader

        output_path = tmp_path / "report.pdf"
        ReportGenerator.generate(sample_analysis_result, output_path)
        reader = PdfReader(str(output_path))
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text() or ""
        assert "膝" in all_text

    def test_generate_with_empty_frames(self, tmp_path):
        """フレームデータが空でもクラッシュしないこと."""
        result_data = {
            "analysis_id": "empty-test",
            "video_info": {"duration": 0, "fps": 30, "width": 1920, "height": 1080},
            "total_frames": 0,
            "frames": [],
            "coaching": {
                "overall_score": 0,
                "summary": "データなし",
                "details": [],
            },
            "ideal_comparison": [],
        }
        output_path = tmp_path / "empty_report.pdf"
        ReportGenerator.generate(result_data, output_path)
        assert output_path.exists()

    def test_generate_with_missing_coaching(self, tmp_path):
        """コーチングデータが欠落していてもクラッシュしないこと."""
        result_data = {
            "analysis_id": "no-coaching",
            "video_info": {"duration": 5, "fps": 30, "width": 1920, "height": 1080},
            "total_frames": 150,
            "frames": [],
            "coaching": {
                "overall_score": 0,
                "summary": "",
                "details": [],
            },
            "ideal_comparison": [],
        }
        output_path = tmp_path / "no_coaching_report.pdf"
        ReportGenerator.generate(result_data, output_path)
        assert output_path.exists()
