# Task Plan: Ski Analyzer 実装更新状況

## Goal
Mock 前提のローカル解析導線を安定化しつつ、real-mode / GPU 準備、artifact 可用性管理、Docker 運用の足場を整える。

## Current Status
- **Phase:** review-driven stabilization complete
- **Branch:** `main`
- **Overall:** mock demo 経路は一貫性を持って動作する状態。status/result/artifact gating の契約は backend / frontend / docs で整合済み。

## Completed

### Backend
- [x] `analysis_pipeline.py` を実装し、result / artifact / report / overlay の保存順序を整理
- [x] `report_generator.py` を atomic write 化し、未完成 PDF を公開しないよう修正
- [x] `overlay_renderer.py` を atomic write 化し、partial MP4 を残さないよう修正
- [x] `/analysis/{id}/status` と `/analysis/{id}/result` に artifact 可用性を反映
- [x] old `result.json` との後方互換を維持
- [x] `download_models.py --check` を追加し、モデル配置確認と exit code を整備
- [x] `USE_MOCK=false` の real-mode は暗黙に mock に落とさず fail-fast に統一
- [x] `Settings.use_mock` の既定値を mock-first に変更

### Frontend
- [x] `useAnalysis` を progressive result loading 対応に更新
- [x] full result は 1 回だけ取得し、その後の artifact 更新は status poll で追従
- [x] `/analyze/:id` 間の遷移で古い result を current 扱いしないよう修正
- [x] `retry()` で polling が再開するよう修正
- [x] DownloadBar / VideoPlayer / analyze page を artifact gating 契約に同期

### Docker / Docs
- [x] `docker-compose.gpu.yml` を追加し、standard demo compose と GPU/real-mode override を分離
- [x] README に mock-first 運用、GPU override、モデル確認手順を反映
- [x] API spec に status/result の `artifacts` 契約を反映

### Tests
- [x] backend: pipeline / integration / report / services / download_models / compose contract を拡充
- [x] frontend: DownloadBar test を追加
- [x] frontend: `useAnalysis` の polling / route change / in-flight fetch / retry をテスト化
- [x] review 指摘ごとの回帰テストを追加

## Validation Snapshot
- Backend:
  - `ruff check app/ tests/`
  - `pytest -q tests/test_services.py tests/test_download_models.py tests/test_pipeline.py tests/test_runtime_contracts.py`
  - `pytest -q tests/test_report_generator.py tests/test_pipeline.py tests/test_integration.py`
- Frontend:
  - `npx tsc --noEmit`
  - `npm run lint`
  - `npm test -- --runInBand`
- Repo:
  - `git diff --check`

## Remaining Work

### Priority 1: 実 HMR 推論統合
- [ ] `pose_estimator.py` の TODO を実実装へ置き換える
- [ ] HMR runtime の import / device / inference / output parsing を実装
- [ ] model files が揃ったときの success path test を追加

### Priority 2: Docker 実行 smoke / E2E
- [ ] standard compose の起動 smoke を自動化
- [ ] GPU override の preflight / startup smoke を自動化
- [ ] upload -> result -> download のブラウザ E2E を追加

### Priority 3: 運用仕上げ
- [ ] matplotlib 日本語フォント warning の整理
- [ ] `PyPDF2` deprecation の整理
- [ ] `CLAUDE.md` と repo 運用文書の最終同期

## Decisions
- Mock-first をデフォルトとする
- real-mode は silent fallback を禁止し、fail-fast を優先する
- artifact 可用性は filesystem truth と atomic write で担保する
- optional artifact 完了前でも result を先出しする

## Notes
- 現時点で main に載っているのは「mock demo を壊さずに進めるための契約整理とテスト拡充」
- 実 HMR 推論そのものは未完了
