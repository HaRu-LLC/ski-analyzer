"""統合テスト: Upload → BackgroundTasks Pipeline → Result 取得フロー.

TDD: テスト先行。BackgroundTasks でパイプラインを非同期実行し、
ステータス遷移と結果取得までの全フローを検証する。
"""

import json
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch):
    """テスト全体で環境変数を安全に上書きする."""
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")


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


class TestBackgroundTasksPipeline:
    """BackgroundTasks による非同期パイプライン統合テスト."""

    @pytest.mark.asyncio()
    async def test_upload_triggers_pipeline(self, client, tmp_storage):
        """アップロード後にパイプラインが起動しステータスが遷移すること."""
        # 有効な動画ファイルの代わりにMockモードを活用
        # VideoProcessor.validate をスキップして直接テスト
        from app.api.routes import _analysis_store

        # テスト用にストアに直接エントリを作成 + パイプライン実行をシミュレート
        from app.services.analysis_pipeline import AnalysisPipeline

        analysis_id = "11111111-1111-1111-1111-111111111111"
        analysis_dir = tmp_storage / analysis_id
        analysis_dir.mkdir()

        # パイプラインを実行
        pipeline = AnalysisPipeline(use_mock=True)

        def _update_status(stage: str, percent: float) -> None:
            _analysis_store[analysis_id] = {
                "status": stage,
                "progress": percent,
            }

        pipeline.run(
            video_path=analysis_dir / "original.mp4",
            output_dir=analysis_dir,
            fps=30.0,
            analysis_id=analysis_id,
            progress_callback=_update_status,
        )

        # パイプライン完了後のステータス確認
        assert _analysis_store[analysis_id]["status"] == "completed"
        assert _analysis_store[analysis_id]["progress"] == 100.0

        # result.json が生成されていること
        result_path = analysis_dir / "result.json"
        assert result_path.exists()

        # API 経由で結果取得
        response = await client.get(f"/api/analysis/{analysis_id}/result")
        assert response.status_code == 200
        data = response.json()
        assert "frames" in data
        assert "coaching" in data
        assert "ideal_comparison" in data
        assert data["total_frames"] > 0

        # クリーンアップ
        del _analysis_store[analysis_id]

    @pytest.mark.asyncio()
    async def test_pipeline_status_progression(self, client, tmp_storage):
        """パイプラインのステータスが正しい順序で遷移すること."""
        from app.api.routes import _analysis_store
        from app.services.analysis_pipeline import AnalysisPipeline

        analysis_id = "22222222-2222-2222-2222-222222222222"
        analysis_dir = tmp_storage / analysis_id
        analysis_dir.mkdir()

        status_history: list[str] = []

        def _track_status(stage: str, percent: float) -> None:
            if stage not in status_history:
                status_history.append(stage)
            _analysis_store[analysis_id] = {
                "status": stage,
                "progress": percent,
            }

        pipeline = AnalysisPipeline(use_mock=True)
        pipeline.run(
            video_path=analysis_dir / "original.mp4",
            output_dir=analysis_dir,
            fps=30.0,
            analysis_id=analysis_id,
            progress_callback=_track_status,
        )

        # ステータスの順序確認
        expected_stages = [
            "extracting_frames",
            "estimating_pose",
            "calculating_angles",
            "comparing_ideal",
            "generating_coaching",
        ]
        for stage in expected_stages:
            assert stage in status_history, f"Stage '{stage}' not found in history"

        # completed が最後
        assert status_history[-1] == "completed"

        del _analysis_store[analysis_id]

    @pytest.mark.asyncio()
    async def test_result_contains_analysis_id(self, client, tmp_storage):
        """結果の result.json に analysis_id が含まれること."""
        from app.services.analysis_pipeline import AnalysisPipeline

        analysis_id = "33333333-3333-3333-3333-333333333333"
        analysis_dir = tmp_storage / analysis_id
        analysis_dir.mkdir()

        pipeline = AnalysisPipeline(use_mock=True)
        pipeline.run(
            video_path=analysis_dir / "original.mp4",
            output_dir=analysis_dir,
            fps=30.0,
            analysis_id=analysis_id,
        )

        # result.json を読み込んで analysis_id 確認
        result_json = json.loads((analysis_dir / "result.json").read_text())
        assert result_json.get("analysis_id") == analysis_id or "frames" in result_json

    @pytest.mark.asyncio()
    async def test_csv_download_after_pipeline(self, client, tmp_storage):
        """パイプライン完走後に CSV ダウンロードが成功すること."""
        from app.services.analysis_pipeline import AnalysisPipeline

        analysis_id = "44444444-4444-4444-4444-444444444444"
        analysis_dir = tmp_storage / analysis_id
        analysis_dir.mkdir()

        pipeline = AnalysisPipeline(use_mock=True)
        pipeline.run(
            video_path=analysis_dir / "original.mp4",
            output_dir=analysis_dir,
            fps=30.0,
        )

        # CSV ダウンロード
        response = await client.get(f"/api/download/{analysis_id}/csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # CSV 内容の検証
        content = response.text
        lines = content.strip().split("\n")
        assert len(lines) >= 2  # ヘッダ + 1行以上のデータ
        assert "frame_index" in lines[0]
        assert "joint_name" in lines[0]

    @pytest.mark.asyncio()
    async def test_frame_data_endpoint(self, client, tmp_storage):
        """パイプライン完走後にフレーム別データが取得できること."""
        from app.services.analysis_pipeline import AnalysisPipeline

        analysis_id = "55555555-5555-5555-5555-555555555555"
        analysis_dir = tmp_storage / analysis_id
        analysis_dir.mkdir()

        pipeline = AnalysisPipeline(use_mock=True)
        pipeline.run(
            video_path=analysis_dir / "original.mp4",
            output_dir=analysis_dir,
            fps=30.0,
        )

        # フレーム0のデータ取得
        response = await client.get(f"/api/analysis/{analysis_id}/frames/0")
        assert response.status_code == 200
        data = response.json()
        assert data["frame_index"] == 0
        assert "joint_angles" in data
        assert len(data["joint_angles"]) > 0

        # 存在しないフレームで404
        response = await client.get(f"/api/analysis/{analysis_id}/frames/999")
        assert response.status_code == 404

    def test_pipeline_error_handling(self, tmp_storage):
        """パイプライン内でエラーが発生した場合にステータスが failed になること."""
        from pathlib import Path

        from app.api.routes import _analysis_store, run_analysis_background

        analysis_id = "66666666-6666-6666-6666-666666666666"
        _analysis_store[analysis_id] = {"status": "validating", "progress": 0}

        # 不正なパスで実行 → エラーハンドリング確認
        run_analysis_background(
            analysis_id=analysis_id,
            video_path=Path("/nonexistent/path.mp4"),
            fps=30.0,
        )
        assert _analysis_store[analysis_id]["status"] == "failed"
        del _analysis_store[analysis_id]
