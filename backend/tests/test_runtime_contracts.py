"""Runtime / compose 契約の軽量テスト."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestComposeContracts:
    """compose ファイルの責務分離を確認する."""

    def test_default_compose_does_not_force_mock_override(self):
        compose_text = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        assert "USE_MOCK=true" not in compose_text

    def test_gpu_override_enables_real_mode(self):
        compose_text = (REPO_ROOT / "docker-compose.gpu.yml").read_text(encoding="utf-8")
        assert "USE_MOCK=false" in compose_text
        assert "Dockerfile.gpu" in compose_text
