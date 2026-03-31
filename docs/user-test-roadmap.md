# User Test Roadmap

## Objective
ユーザーテスト実施までに、UI/導線確認と実解析確認の両方を成立させる。

## Current State
- Mock 前提の upload -> status -> result -> artifact gating は安定している
- `StatusResponse.artifacts` / `AnalysisResult.artifacts` の契約は backend / frontend / docs で整合済み
- real-mode (`USE_MOCK=false`) は fail-fast 契約まで完了しているが、実 HMR 推論そのものは未統合
- GPU override compose とモデル確認 CLI はあるが、実動画を使った GPU 通し確認は未実施

## Delivery Phases

### Phase 1: Test-First Requirements Lock
- Backend:
  - real-mode success path 用の contract test を追加
  - モデル不足、runtime import failure、GPU 非検出、推論失敗の test を追加
  - pipeline real-mode 統合 test を追加
- Frontend:
  - `/analyze/:id` の受け入れ test を追加
  - completed 前 progressive result 表示の UI test を追加
  - failed / retry / route change の UX test を追加
  - artifact 更新による download / video availability 反映 test を追加
- Docker / smoke:
  - standard compose mock smoke
  - GPU override real-mode preflight smoke
  - `download_models --check` の preflight success/failure を固定

### Phase 2: Real-Mode Implementation
- `pose_estimator.py` の TODO を実装
  - runtime import
  - device selection
  - model load
  - frame inference
  - output parsing
- `analysis_pipeline.py` の real-mode 成功経路を完走させる
- `download_models.py` の success path を明確化する
- mock fallback は入れず、real-mode は explicit/fail-fast を維持する

### Phase 3: GPU Environment Readiness
- `docker-compose.gpu.yml` を実起動確認済み構成に仕上げる
- GPU セットアップガイドを追加
  - NVIDIA driver
  - Docker / NVIDIA Container Toolkit
  - `.env` 切り替え
  - モデル配置
  - 起動手順
  - 典型エラーと対処
- README の standard compose / GPU compose の責務を最終同期する

### Phase 4: User-Test Rehearsal
- 実動画で upload -> progress -> result -> download を通す
- 最低 3 ケースを確認
  - 正常動画
  - 長め動画
  - エラー動画
- ユーザーテスト実施ガイドをまとめる
  - 手順
  - 観察ポイント
  - 既知制約
  - ログ採取方法
  - 障害時の切り戻し

## Detailed Design Check

### Backend
- `PoseEstimator`:
  - 現状は required files check と fail-fast のみ
  - 実装時は `estimate_frame()` の返却 shape を現行 pipeline 契約に合わせる必要がある
  - `analysis_pipeline.py` は pose 結果の `joint_positions_3d`, `joint_rotations`, `smpl_params` を前提にしている
- `AnalysisPipeline`:
  - core `result.json` 先行保存 + optional artifact 更新保存の設計は維持でよい
  - real-mode 実装後も artifact availability の source of truth は filesystem のまま維持する
- `download_models.py`:
  - 現状の `--check` は配置確認のみ
  - success path 実装時は「どのファイルが揃えば real-mode 可か」を runtime 実装と一致させる必要がある

### Frontend
- `useAnalysis`:
  - full result は初回のみ取得、artifact は status poll で追従する設計でよい
  - real-mode 化して result が大きくなっても、現行の負荷方針は維持可能
- `AnalyzePage`:
  - result 到着前は progress、到着後は completed 前でも本画面表示の方針でよい
  - ユーザーテストでは completed 前表示が混乱を生まないかを確認項目に入れる

### Docker / Environment
- `docker-compose.gpu.yml`:
  - build はあるが、実行に必要な model mount / host prerequisites / runtime availability が文書化不足
  - ユーザーテスト前に「実行環境構築手順」と「失敗時の診断手順」を必須で追加する

## Acceptance Criteria
- real-mode の成功/失敗条件が test で固定されている
- GPU 環境で README / ガイドどおりに backend を起動できる
- 実動画 E2E を少なくとも 1 回成功させている
- ユーザーテスト担当者が手順書だけで起動・実施できる

## Risks
- 実 HMR runtime の依存関係が `requirements.txt` だけでは不足する可能性が高い
- GPU/container 前提条件がホスト依存なので、セットアップガイドなしでは再現性が低い
- 実解析品質の評価観点が未定義だと、ユーザーテスト結果が UI 所感に偏る
