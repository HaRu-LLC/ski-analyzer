# Code Review Guidance

レビューでは要約より findings を優先する。以下の順で確認する。

1. 動作回帰
2. API 契約の破壊
3. 非同期処理や重い処理の詰まり
4. テスト不足
5. ドキュメントや運用手順の不整合

## Repo-specific risks

- `backend/app/schemas/` と `frontend/src/types/analysis.ts` の shape ずれ
- `frontend/src/utils/api.ts` が期待するエンドポイントと `backend/app/api/routes.py` の不一致
- `analysis_pipeline.py` 変更に伴う `report_generator.py`、`overlay_renderer.py`、`coaching_generator.py` への波及
- 正面カメラ 1 台の精度制約を無視した UI 表示
- agent 出力が入力メトリクスにない主張をしていないか
- 低信頼の前傾・回旋を断定していないか
- fallback や review reject で public API shape が壊れていないか

## Expected review output

- findings を重大度順に並べる
- 各 finding にファイルと行番号を付ける
- 問題がない場合はその旨を明記し、残るリスクや未検証点だけを補足する
