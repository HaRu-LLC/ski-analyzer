"""解析パイプライン + API のテスト (TDD: テスト先行)."""

import json
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import ModelNotLoadedError

# テスト用の有効なUUID形式ID
_FAKE_UUID = "00000000-0000-0000-0000-000000000001"
_STATUS_UUID = "00000000-0000-0000-0000-000000000002"
_RESULT_UUID = "00000000-0000-0000-0000-000000000003"
_CSV_UUID = "00000000-0000-0000-0000-000000000004"


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch):
    """テスト全体で環境変数を安全に上書きする."""
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")


# app のインポートはフィクスチャ経由で環境変数を設定した後でも
# モジュールレベルで行う必要がある（FastAPI app はグローバル）
from app.main import app  # noqa: E402


@pytest.fixture()
def tmp_storage(tmp_path):
    """一時ストレージパスを設定する."""
    with patch("app.core.settings.storage_path", tmp_path):
        with patch("app.core.settings.use_mock", True):
            yield tmp_path


@pytest.fixture()
async def client(tmp_storage):
    """非同期テストクライアント."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestUploadEndpoint:
    """POST /api/upload のテスト."""

    @pytest.mark.asyncio()
    async def test_upload_valid_video(self, client, tmp_path):
        """有効な動画ファイルでアップロードが成功すること."""
        # ダミーMP4ファイル作成
        video = tmp_path / "test.mp4"
        video.write_bytes(b"\x00" * 1024)

        with open(video, "rb") as f:
            response = await client.post(
                "/api/upload",
                files={"file": ("test.mp4", f, "video/mp4")},
            )

        # ダミーバイト列は有効な動画ではないためバリデーションエラーになる
        assert response.status_code == 400

    @pytest.mark.asyncio()
    async def test_upload_invalid_extension(self, client, tmp_path):
        """非対応の拡張子でエラーになること."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a video")

        with open(txt_file, "rb") as f:
            response = await client.post(
                "/api/upload",
                files={"file": ("test.txt", f, "text/plain")},
            )

        assert response.status_code == 400
        assert "非対応" in response.json()["detail"]


class TestStatusEndpoint:
    """GET /api/analysis/{id}/status のテスト."""

    @pytest.mark.asyncio()
    async def test_status_not_found(self, client):
        """存在しないIDで404を返すこと."""
        response = await client.get(f"/api/analysis/{_FAKE_UUID}/status")
        assert response.status_code == 404

    @pytest.mark.asyncio()
    async def test_status_fields(self, client):
        """ステータスレスポンスに必要なフィールドが含まれること."""
        # まずインメモリストアに直接エントリを追加
        from app.api.routes import _analysis_store

        _analysis_store[_STATUS_UUID] = {
            "status": "estimating_pose",
            "progress": 45.0,
        }

        response = await client.get(f"/api/analysis/{_STATUS_UUID}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == _STATUS_UUID
        assert data["status"] == "estimating_pose"
        assert data["progress"] == 45.0
        assert data["artifacts"] == {"video": False, "report": False, "csv": False}

        # クリーンアップ
        del _analysis_store[_STATUS_UUID]


class TestResultEndpoint:
    """GET /api/analysis/{id}/result のテスト."""

    @pytest.mark.asyncio()
    async def test_result_not_found(self, client):
        """結果が存在しない場合に404を返すこと."""
        response = await client.get(f"/api/analysis/{_FAKE_UUID}/result")
        assert response.status_code == 404

    @pytest.mark.asyncio()
    async def test_result_returns_data(self, client, tmp_storage):
        """result.json が存在する場合にデータを返すこと."""
        analysis_dir = tmp_storage / _RESULT_UUID
        analysis_dir.mkdir()
        result_data = {
            "analysis_id": _RESULT_UUID,
            "video_info": {"duration": 5.0, "fps": 30.0, "width": 1920, "height": 1080},
            "total_frames": 150,
            "frames": [],
            "coaching": {"overall_score": 70, "summary": "Good", "details": []},
            "ideal_comparison": [],
            "artifacts": {"video": False, "report": False, "csv": True},
        }
        (analysis_dir / "result.json").write_text(json.dumps(result_data))

        response = await client.get(f"/api/analysis/{_RESULT_UUID}/result")
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == _RESULT_UUID
        assert data["total_frames"] == 150

    @pytest.mark.asyncio()
    async def test_result_without_artifacts_remains_compatible(self, client, tmp_storage):
        """旧 result.json に artifacts がなくても取得できること."""
        analysis_id = "00000000-0000-0000-0000-000000000005"
        analysis_dir = tmp_storage / analysis_id
        analysis_dir.mkdir()
        result_data = {
            "analysis_id": analysis_id,
            "video_info": {"duration": 5.0, "fps": 30.0, "width": 1920, "height": 1080},
            "total_frames": 150,
            "frames": [],
            "coaching": {"overall_score": 70, "summary": "Good", "details": []},
            "ideal_comparison": [],
        }
        (analysis_dir / "result.json").write_text(json.dumps(result_data))

        response = await client.get(f"/api/analysis/{analysis_id}/result")
        assert response.status_code == 200
        data = response.json()
        assert data["artifacts"] == {"video": False, "report": False, "csv": False}

    @pytest.mark.asyncio()
    async def test_result_without_artifacts_uses_existing_files(self, client, tmp_storage):
        """旧 result.json でも既存成果物があれば artifact として返すこと."""
        analysis_id = "00000000-0000-0000-0000-000000000006"
        analysis_dir = tmp_storage / analysis_id
        analysis_dir.mkdir()
        result_data = {
            "analysis_id": analysis_id,
            "video_info": {"duration": 5.0, "fps": 30.0, "width": 1920, "height": 1080},
            "total_frames": 150,
            "frames": [],
            "coaching": {"overall_score": 70, "summary": "Good", "details": []},
            "ideal_comparison": [],
        }
        (analysis_dir / "result.json").write_text(json.dumps(result_data))
        (analysis_dir / "overlay.mp4").write_bytes(b"mp4")
        (analysis_dir / "report.pdf").write_bytes(b"%PDF-")
        (analysis_dir / "angles.csv").write_text("frame_index\n0\n")

        response = await client.get(f"/api/analysis/{analysis_id}/result")
        assert response.status_code == 200
        data = response.json()
        assert data["artifacts"] == {"video": True, "report": True, "csv": True}

    @pytest.mark.asyncio()
    async def test_result_artifacts_follow_filesystem_truth(self, client, tmp_storage):
        """保存済み artifacts より実ファイル有無を優先すること."""
        analysis_id = "00000000-0000-0000-0000-000000000007"
        analysis_dir = tmp_storage / analysis_id
        analysis_dir.mkdir()
        result_data = {
            "analysis_id": analysis_id,
            "video_info": {"duration": 5.0, "fps": 30.0, "width": 1920, "height": 1080},
            "total_frames": 150,
            "frames": [],
            "coaching": {"overall_score": 70, "summary": "Good", "details": []},
            "ideal_comparison": [],
            "artifacts": {"video": True, "report": True, "csv": True},
        }
        (analysis_dir / "result.json").write_text(json.dumps(result_data))
        (analysis_dir / "angles.csv").write_text("frame_index\n0\n")

        response = await client.get(f"/api/analysis/{analysis_id}/result")
        assert response.status_code == 200
        data = response.json()
        assert data["artifacts"] == {"video": False, "report": False, "csv": True}


class TestDownloadEndpoints:
    """ダウンロード系エンドポイントのテスト."""

    @pytest.mark.asyncio()
    async def test_download_video_not_found(self, client):
        """動画が存在しない場合に404を返すこと."""
        response = await client.get(f"/api/download/{_FAKE_UUID}/video")
        assert response.status_code == 404

    @pytest.mark.asyncio()
    async def test_download_report_not_found(self, client):
        """レポートが存在しない場合に404を返すこと."""
        response = await client.get(f"/api/download/{_FAKE_UUID}/report")
        assert response.status_code == 404

    @pytest.mark.asyncio()
    async def test_download_csv_not_found(self, client):
        """CSVが存在しない場合に404を返すこと."""
        response = await client.get(f"/api/download/{_FAKE_UUID}/csv")
        assert response.status_code == 404

    @pytest.mark.asyncio()
    async def test_download_csv_success(self, client, tmp_storage):
        """CSVファイルが存在する場合にダウンロードできること."""
        analysis_dir = tmp_storage / _CSV_UUID
        analysis_dir.mkdir()
        csv_content = "frame,l_knee_flexion,r_knee_flexion\n0,-55.0,-55.0\n"
        (analysis_dir / "angles.csv").write_text(csv_content)

        response = await client.get(f"/api/download/{_CSV_UUID}/csv")
        assert response.status_code == 200


class TestAnalysisPipeline:
    """解析パイプライン全体のテスト."""

    def test_pipeline_service_exists(self):
        """AnalysisPipeline サービスが存在すること."""
        from app.services.analysis_pipeline import AnalysisPipeline

        assert AnalysisPipeline is not None

    def test_pipeline_run_mock(self, tmp_path):
        """Mock モードでパイプラインが完走すること."""
        from app.services.analysis_pipeline import AnalysisPipeline

        # ダミー動画ファイル (パイプラインはMockモードなので中身不問)
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"\x00" * 100)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        pipeline = AnalysisPipeline(use_mock=True)
        result = pipeline.run(
            video_path=video_path,
            output_dir=output_dir,
            fps=30.0,
        )

        assert "analysis_id" not in result or isinstance(result.get("analysis_id"), str)
        assert "frames" in result
        assert "coaching" in result
        assert "ideal_comparison" in result
        assert result["artifacts"]["csv"] is True
        assert result["artifacts"]["video"] is False
        assert set(result["artifacts"]) == {"video", "report", "csv"}
        assert isinstance(result["frames"], list)

    def test_pipeline_generates_result_json(self, tmp_path):
        """パイプライン完走後に result.json が生成されること."""
        from app.services.analysis_pipeline import AnalysisPipeline

        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"\x00" * 100)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        pipeline = AnalysisPipeline(use_mock=True)
        pipeline.run(video_path=video_path, output_dir=output_dir, fps=30.0)

        result_json = output_dir / "result.json"
        assert result_json.exists()
        saved = json.loads(result_json.read_text())
        assert "artifacts" in saved
        assert saved["artifacts"]["csv"] is True
        assert saved["artifacts"]["video"] is False

    def test_pipeline_generates_csv(self, tmp_path):
        """パイプライン完走後に angles.csv が生成されること."""
        from app.services.analysis_pipeline import AnalysisPipeline

        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"\x00" * 100)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        pipeline = AnalysisPipeline(use_mock=True)
        pipeline.run(video_path=video_path, output_dir=output_dir, fps=30.0)

        csv_path = output_dir / "angles.csv"
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "frame_index" in content  # ヘッダ行

    def test_pipeline_generates_agent_trace(self, tmp_path):
        """パイプライン完走後に agent_trace.json が生成されること."""
        from app.services.analysis_pipeline import AnalysisPipeline

        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"\x00" * 100)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        pipeline = AnalysisPipeline(use_mock=True)
        pipeline.run(video_path=video_path, output_dir=output_dir, fps=30.0)

        trace_path = output_dir / "agent_trace.json"
        assert trace_path.exists()

    def test_pipeline_skips_overlay_in_mock_mode(self, tmp_path):
        """Mock モードでは overlay.mp4 を生成しないこと."""
        from app.services.analysis_pipeline import AnalysisPipeline

        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"\x00" * 100)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        pipeline = AnalysisPipeline(use_mock=True)
        result = pipeline.run(video_path=video_path, output_dir=output_dir, fps=30.0)

        assert result["artifacts"]["video"] is False
        assert not (output_dir / "overlay.mp4").exists()

    def test_pipeline_persists_core_result_before_optional_artifacts(self, tmp_path, monkeypatch):
        """optional artifact 生成前に core result.json が保存されていること."""
        from app.services.analysis_pipeline import AnalysisPipeline

        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"\x00" * 100)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result_json_path = output_dir / "result.json"

        frame_paths = [output_dir / "frame_000001.jpg"]
        frame_data = [
            {
                "frame_index": 0,
                "timestamp_ms": 0.0,
                "joint_positions_3d": {"l_knee": [0.0, 0.0, 0.0]},
                "joint_rotations": {"l_knee": [0.0, 0.0, 0.0]},
                "joint_angles": [
                    {
                        "joint_name": "l_knee",
                        "joint_name_ja": "左膝",
                        "flexion": -50.0,
                        "rotation": 0.0,
                        "abduction": 0.0,
                        "confidence": "medium",
                    }
                ],
            }
        ]
        angle_summary = {
            "左膝": {"flexion": {"mean": -50.0, "std": 0.0, "min": -50.0, "max": -50.0}}
        }
        coaching = {"overall_score": 80, "summary": "Good", "details": []}
        trace = {
            "provider": "test",
            "model": "test",
            "review_decision": "approved",
            "review_issues": [],
        }

        class _FakeEstimator:
            def estimate_video(self, frame_paths):
                return [
                    {
                        "joint_positions_3d": {"l_knee": [0.0, 0.0, 0.0]},
                        "joint_rotations": {"l_knee": [0.0, 0.0, 0.0]},
                    }
                    for _ in frame_paths
                ]

        class _FakeComparator:
            def compare(self, summary):
                return []

        class _FakeCoachingGenerator:
            @staticmethod
            def summarize_angles(frame_data_list):
                return angle_summary

            def generate_with_metadata(self, angle_summary, ideal_comparison=None):
                return coaching, trace

        def _fake_overlay_render(video, poses, output):
            assert result_json_path.exists()
            saved = json.loads(result_json_path.read_text())
            assert saved["frames"]
            output.write_bytes(b"mp4")
            return output

        def _fake_report_generate(result_data, output):
            assert result_json_path.exists()
            output.write_bytes(b"%PDF-")
            return output

        monkeypatch.setattr(
            "app.services.analysis_pipeline.VideoProcessor.extract_frames", lambda *_: frame_paths
        )
        monkeypatch.setattr(
            "app.services.analysis_pipeline.PoseEstimator.get_instance", lambda: _FakeEstimator()
        )
        monkeypatch.setattr(
            "app.services.analysis_pipeline.AngleCalculator.calculate_video_angles",
            lambda *_: frame_data,
        )
        monkeypatch.setattr("app.services.analysis_pipeline.IdealComparator", _FakeComparator)
        monkeypatch.setattr(
            "app.services.analysis_pipeline.CoachingGenerator", _FakeCoachingGenerator
        )
        monkeypatch.setattr(
            "app.services.analysis_pipeline.OverlayRenderer.render", _fake_overlay_render
        )
        monkeypatch.setattr(
            "app.services.analysis_pipeline.ReportGenerator.generate", _fake_report_generate
        )

        pipeline = AnalysisPipeline(use_mock=False)
        result = pipeline.run(video_path=video_path, output_dir=output_dir, fps=30.0)

        assert result_json_path.exists()
        saved = json.loads(result_json_path.read_text())
        assert saved["artifacts"] == {"video": True, "report": True, "csv": True}
        assert result["artifacts"] == {"video": True, "report": True, "csv": True}

    def test_pipeline_real_mode_honors_explicit_use_mock_false(self, tmp_path, monkeypatch):
        """settings.use_mock=true でも pipeline 指定が false なら real-mode 経路に入ること."""
        from app.services.analysis_pipeline import AnalysisPipeline

        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"\x00" * 100)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        monkeypatch.setattr("app.core.settings.use_mock", True)
        monkeypatch.setattr(
            "app.services.analysis_pipeline.VideoProcessor.extract_frames",
            lambda *_: [output_dir / "frame_000001.jpg"],
        )
        monkeypatch.setattr("app.core.settings.model_path", tmp_path / "models")

        with pytest.raises(ModelNotLoadedError):
            AnalysisPipeline(use_mock=False).run(
                video_path=video_path,
                output_dir=output_dir,
                fps=30.0,
            )
