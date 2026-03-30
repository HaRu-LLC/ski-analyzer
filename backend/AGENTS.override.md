# Backend Override

このディレクトリ配下では Python / FastAPI 側の規約を優先する。

## Focus

- 主対象は `app/` と `tests/`
- API 変更時は `app/schemas/` と `app/api/routes.py` を起点に影響範囲を確認する
- 解析パイプライン変更時は `app/services/analysis_pipeline.py` を中心に、`video_processor.py`、`pose_estimator.py`、`coaching_generator.py`、`report_generator.py` を確認する

## Validation

- 基本: `ruff check app/`
- フォーマット確認: `ruff format --check app/`
- テスト: `pytest tests/ -v`
- GPU や外部モデルに依存しない確認を優先し、必要に応じて `USE_MOCK=true` を使う

## Guardrails

- 型ヒントと docstring を維持する
- 例外やレスポンス shape を変える場合はフロントエンド側への影響を確認する
- 重い処理を追加する場合は同期 API を詰まらせないようにする
