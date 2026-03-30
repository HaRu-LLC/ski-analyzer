"""HMRモデルダウンロードスクリプト.

初回セットアップ時に実行:
    python -m app.scripts.download_models
"""

import logging

from app.core import settings

logger = logging.getLogger(__name__)

# モデル定義（download_models / check_models で共有）
MODELS: dict[str, dict[str, str]] = {
    "hmr2": {
        "url": "https://github.com/shubham-goel/4D-Humans/releases/download/v1.0/hmr2_model.pt",
        "filename": "hmr2_model.pt",
        "description": "HMR2.0 pretrained model",
    },
    "smpl": {
        "url": "https://download.is.tue.mpg.de/download.php?domain=smpl&sfile=SMPL_python_v.1.1.0.zip",
        "filename": "SMPL_NEUTRAL.pkl",
        "description": "SMPL body model (要ライセンス同意)",
    },
}


def download_models():
    """必要なモデルファイルをダウンロードする."""
    model_dir = settings.model_path
    model_dir.mkdir(parents=True, exist_ok=True)

    print(f"Model directory: {model_dir}")

    for name, info in MODELS.items():
        target = model_dir / info["filename"]
        if target.exists():
            print(f"  [SKIP] {name}: {info['filename']} already exists")
        else:
            print(f"  [TODO] {name}: {info['description']}")
            print(f"         Download from: {info['url']}")
            print(f"         Save to: {target}")

    print()
    print("Note: SMPLモデルの利用にはライセンスへの同意が必要です。")
    print("      https://smpl.is.tue.mpg.de/ から登録してダウンロードしてください。")


def check_models() -> dict:
    """Check which models are available.

    Returns:
        Dict with model name as key, and dict with 'exists' (bool),
        'filename', 'description' as value.
    """
    model_dir = settings.model_path
    result = {}
    for name, info in MODELS.items():
        target = model_dir / info["filename"]
        result[name] = {
            "exists": target.exists(),
            "filename": info["filename"],
            "description": info["description"],
        }
    return result


if __name__ == "__main__":
    download_models()
