# Task Plan: User Test Readiness

## Goal
ユーザーテスト実施までに、UI/導線確認と実解析確認の両方を成立させる。

## Current Status
- **Phase:** pre-user-test planning
- **Overall:** mock-first demo は安定、real-mode 実推論は未完了
- **Source doc:** `docs/user-test-roadmap.md`

## Completed

### Mock Demo Stabilization
- [x] upload -> status -> result -> artifact gating を安定化
- [x] `StatusResponse.artifacts` / `AnalysisResult.artifacts` を導入
- [x] result / report / overlay の atomic write 化
- [x] old `result.json` との互換維持
- [x] frontend の progressive result loading と retry を安定化

### Test Foundation
- [x] backend unit / integration / pipeline / report / runtime contract tests を拡充
- [x] frontend component / hook tests を拡充
- [x] review 指摘を回帰テストで固定

### Environment Preparation
- [x] `download_models.py --check` を追加
- [x] `docker-compose.gpu.yml` を追加
- [x] README / API spec を現状契約に同期

## Remaining Work

### Phase 1: Test-First User-Test Requirements
- [ ] backend real-mode success path test を追加
- [ ] backend real-mode failure mode test を拡張
- [ ] frontend `/analyze/:id` 受け入れ test を追加
- [ ] frontend artifact-driven UX test を追加
- [ ] standard compose mock smoke test を追加
- [ ] GPU override preflight smoke test を追加

### Phase 2: Real-Mode Implementation
- [ ] `pose_estimator.py` の TODO を実装
- [ ] HMR runtime import / model load / inference / output parsing を実装
- [ ] `analysis_pipeline.py` の real-mode 完走経路を成立させる
- [ ] `download_models.py --check` の success path を runtime 実装に合わせて確定

### Phase 3: GPU Environment Readiness
- [ ] GPU セットアップガイドを作成
- [ ] `docker-compose.gpu.yml` の実起動確認
- [ ] model mount / env / host prerequisites を文書化

### Phase 4: User-Test Rehearsal
- [ ] 実動画 E2E を実施
- [ ] 正常動画 / 長め動画 / エラー動画の 3 ケース確認
- [ ] ユーザーテスト実施ガイドを作成

## Detailed Design Notes
- real-mode は silent fallback を入れず fail-fast を維持する
- artifact availability の source of truth は filesystem のまま維持する
- full result は初回取得のみ、artifact 更新は status poll で追従する
- GPU 環境前提条件はホスト依存なので、手順書を実装と同じ優先度で扱う

## Validation Gates
- Backend:
  - `ruff check app/ tests/`
  - `pytest -q`
- Frontend:
  - `npx tsc --noEmit`
  - `npm run lint`
  - `npm test -- --runInBand`
- User-test preflight:
  - `python -m app.scripts.download_models --check`
  - compose smoke
  - 実動画 E2E 1 回成功

## Risks
- 実 HMR runtime の依存が不足している可能性
- GPU / container prerequisites の再現性不足
- 実解析品質の評価基準が曖昧なまま進むと、ユーザーテスト結果が判断しづらい
