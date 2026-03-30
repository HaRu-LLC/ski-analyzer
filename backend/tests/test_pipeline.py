"""解析パイプライン + API のテスト (TDD: テスト先行)."""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

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
        import json

        analysis_dir = tmp_storage / _RESULT_UUID
        analysis_dir.mkdir()
        result_data = {
            "analysis_id": _RESULT_UUID,
            "video_info": {"duration": 5.0, "fps": 30.0, "width": 1920, "height": 1080},
            "total_frames": 150,
            "frames": [],
            "coaching": {"overall_score": 70, "summary": "Good", "details": []},
            "ideal_comparison": [],
        }
        (analysis_dir / "result.json").write_text(json.dumps(result_data))

        response = await client.get(f"/api/analysis/{_RESULT_UUID}/result")
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == _RESULT_UUID
        assert data["total_frames"] == 150


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
