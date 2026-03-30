"""モデルダウンロードスクリプトのテスト (TDD: テスト先行)."""

from unittest.mock import patch


class TestDownloadModels:
    """download_models スクリプトのテスト."""

    def test_creates_model_directory(self, tmp_path):
        """モデルディレクトリが存在しない場合に作成されること."""
        model_dir = tmp_path / "models"
        assert not model_dir.exists()

        with patch("app.core.settings.model_path", model_dir):
            from app.scripts.download_models import download_models

            download_models()

        assert model_dir.exists()

    def test_skips_existing_model(self, tmp_path, capsys):
        """既存のモデルファイルをスキップすること."""
        model_dir = tmp_path / "models"
        model_dir.mkdir()
        (model_dir / "hmr2_model.pt").write_bytes(b"fake model")

        with patch("app.core.settings.model_path", model_dir):
            from app.scripts.download_models import download_models

            download_models()

        output = capsys.readouterr().out
        assert "SKIP" in output

    def test_shows_todo_for_missing_model(self, tmp_path, capsys):
        """不足モデルに対してダウンロード指示を表示すること."""
        model_dir = tmp_path / "models"
        model_dir.mkdir()

        with patch("app.core.settings.model_path", model_dir):
            from app.scripts.download_models import download_models

            download_models()

        output = capsys.readouterr().out
        assert "TODO" in output or "Download" in output

    def test_shows_smpl_license_notice(self, tmp_path, capsys):
        """SMPLライセンス注意書きが表示されること."""
        model_dir = tmp_path / "models"
        model_dir.mkdir()

        with patch("app.core.settings.model_path", model_dir):
            from app.scripts.download_models import download_models

            download_models()

        output = capsys.readouterr().out
        assert "ライセンス" in output or "smpl" in output.lower()

    def test_check_models_function(self, tmp_path):
        """check_models がモデル配置状態を dict で返すこと."""
        model_dir = tmp_path / "models"
        model_dir.mkdir()
        (model_dir / "hmr2_model.pt").write_bytes(b"fake")

        with patch("app.core.settings.model_path", model_dir):
            from app.scripts.download_models import check_models

            status = check_models()

        assert isinstance(status, dict)
        assert "hmr2" in status
        assert status["hmr2"]["exists"] is True
        assert "smpl" in status
        assert status["smpl"]["exists"] is False

    def test_validate_models_reports_missing(self, tmp_path):
        """validate_models が不足モデル名を返すこと."""
        model_dir = tmp_path / "models"
        model_dir.mkdir()
        (model_dir / "hmr2_model.pt").write_bytes(b"fake")

        with patch("app.core.settings.model_path", model_dir):
            from app.scripts.download_models import validate_models

            ok, missing = validate_models()

        assert ok is False
        assert missing == ["smpl"]

    def test_main_check_returns_nonzero_when_models_missing(self, tmp_path, capsys):
        """--check は不足時に非ゼロ終了すること."""
        model_dir = tmp_path / "models"
        model_dir.mkdir()

        with patch("app.core.settings.model_path", model_dir):
            from app.scripts.download_models import main

            exit_code = main(["--check"])

        output = capsys.readouterr().out
        assert exit_code == 1
        assert "MISSING" in output
