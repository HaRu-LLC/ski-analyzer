# Findings & Decisions

## Requirements
- 室内スキーシミュレータの滑走動画をアップロードし AI で解析
- 3D 姿勢推定 (SMPL ベース HMR) + 関節角度算出
- 理想フォームとの比較 + AI コーチング (Claude API)
- スケルトン重畳動画 / PDF レポート / CSV データのダウンロード
- ログイン不要、セッション ID ベースで管理
- 動画は 24 時間後に自動削除

## Research Findings

### プロジェクト実装状況 (2026-03-30 調査)

**Frontend (実装率 ~90%)**
- Next.js 14 (App Router) + TypeScript で構築済み
- VideoUploader, VideoPlayer, ProgressIndicator, AnglePanel, AngleGraph, CoachingPanel, DownloadBar: 全て実装済み
- VideoPlayer: 2D Canvas フォールバックで動作するが Three.js 3D スケルトンは TODO (L77)
- SkeletonOverlay: `return null` のプレースホルダー
- IdealComparison: `return null` のプレースホルダー
- Zustand で状態管理、Recharts でグラフ描画

**Backend (実装率 ~85%)**
- FastAPI + Python 3.11、全 API エンドポイント実装済み
- `video_processor.py`: FFprobe バリデーション + FFmpeg フレーム抽出 — 完全実装
- `pose_estimator.py`: Mock モード動作可、**実 HMR モデルロード未実装** (L72-76, L106-110)
- `angle_calculator.py`: axis-angle → Euler 変換 — 完全実装 (scipy 使用)
- `ideal_comparator.py`: 理想フォームデータ + 許容範囲ベース評価 — 完全実装
- `coaching_generator.py`: Claude API 統合 — 完全実装 (API キーなし時の fallback あり)
- `overlay_renderer.py`: OpenCV スケルトン描画 + FFmpeg H.264 再エンコード — 完全実装
- `report_generator.py`: **未実装 stub** — reportlab + matplotlib で TODO
- `download_models.py`: **未実装** — URL リスト + 手動ダウンロード指示のみ
- `routes.py`: インメモリ dict で管理 — **Celery タスク移行 TODO** (L63)

**Models**
- `face_mesh.py`: MediaPipe Face Mesh 468 ランドマーク → solvePnP で 3D 頭部回転 — 完全実装
- `smpl.py`: smplx ライブラリラッパー — 完全実装 (モデルファイル不在時のダミー fallback あり)

**Infrastructure**
- docker-compose.yml: 4 サービス (frontend, backend, worker, redis) — GPU サポートあり
- Dockerfile (frontend/backend): マルチステージビルド — 完全
- Dockerfile.gpu: CUDA 12.1.1 ベース — 完全
- nginx.conf: リバースプロキシ 500MB アップロード対応 — 完全
- CI/CD (.github/workflows/ci.yml): Python 3.11 + Node 20 テストマトリクス — 完全

**Tests**
- `backend/tests/test_services.py`: AngleCalculator, PoseEstimator (mock), IdealComparator のテストあり
- Frontend テスト: CI で Jest 参照されているが、テストファイルの有無は未確認

### TODO/FIXME コメント一覧
| ファイル | 行 | 内容 |
|---------|-----|------|
| `backend/app/api/routes.py` | 63 | Celery タスク統合 |
| `backend/app/services/pose_estimator.py` | 72-76 | HMR モデルローディング |
| `backend/app/services/pose_estimator.py` | 106-110 | HMR 推論実行 |
| `backend/app/services/report_generator.py` | 12-19 | PDF レポート生成 |
| `backend/app/scripts/download_models.py` | 22 | モデルダウンロードロジック |
| `frontend/src/components/VideoPlayer.tsx` | 77 | Three.js 3D スケルトン |
| `frontend/src/components/SkeletonOverlay.tsx` | 6-10 | Three.js 実装 |
| `frontend/src/components/IdealComparison.tsx` | 4-6 | コンポーネント実装 |

## 確定仕様 (2026-03-30 ユーザー承認済み)

### PDF レポート
- 日本語のみ
- セクション: 表紙 → 総合スコア → 部位別角度サマリー → 時系列グラフ (膝・股関節・肩の屈曲角度) → 理想フォーム比較表 → AIコーチング
- ページ数: 要件駆動 (内容に必要なだけ)
- デザイン: プレーン (ロゴ・ブランド要素なし)

### HMR モデル統合
- Mock モードを品質優先で維持 (テストカバレッジ拡充が主目的)
- 実モデル統合は将来タスク (ユーザー動作確認時に CPU fallback 検討)
- インターフェースを固定し、Mock/Real を切り替え可能にする

### 解析パイプライン
- FastAPI BackgroundTasks で非同期化 (Celery は過剰)
- 単一パイプラインタスク (フレーム抽出 → ポーズ推定 → 角度算出 → コーチング → レンダリング → レポート)
- ユーザーが動作確認できることが最優先

### モデルダウンロード
- 手動ダウンロード + 配置確認 + ガイド表示の方式

### Frontend スケルトン
- 2D Canvas 描画を維持・改善 (Three.js は将来)
- 関節の精度レベル色分け実装 (見やすさ優先: high=緑, medium=黄, low=赤)

### IdealComparison
- テーブル/リスト形式の比較表示で十分 (スケルトン並列表示は将来)

### テスト環境
- Frontend: Jest + React Testing Library セットアップ
- 見やすさ・UX 優先の方針

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| SMPL ベース HMR (HMR2) を姿勢推定に使用 | 24 関節の 3D パラメトリックモデル、axis-angle 出力で関節角度算出に直結 |
| MediaPipe Face Mesh で頭部回転補完 | HMR は顔の詳細回転が弱いため 468 ランドマークで補完 |
| Mock モードをデフォルト開発設定に | GPU 不要でフルパイプライン動作確認可能 |
| Claude API でコーチングテキスト生成 | 関節角度データを構造化してプロンプトに渡し、自然言語アドバイスを生成 |
| 正面カメラ1台の精度制約を UI に反映 | Z軸回転は「参考値」ラベル付与、確信度3段階表示 |
| FastAPI BackgroundTasks で非同期化 | Celery+Redis は動作確認目的では過剰。まず動くものを優先 |
| 2D Canvas スケルトン維持 | Three.js は過剰。2D + 色分けで見やすさ確保が先 |
| PDF レポート日本語のみ | ユーザーは日本語話者、i18n は将来 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Git リポジトリ未初期化と思ったが既に .git 存在 | `git init` 再実行で確認、main ブランチ + 1 コミット存在 |
| FFmpeg 未インストール | `brew install ffmpeg` バックグラウンド実行中 |
| Frontend Jest 未設定 | devDependencies に jest, @testing-library/react 等を追加予定 |
| Frontend .eslintrc.json 未作成 | `next/core-web-vitals` 設定で作成済み |
| Ruff lint 6 errors | unused imports 5 件 (auto-fix 可), naming convention 1 件 (R → r) |

### 環境情報
| Tool | Version | Status |
|------|---------|--------|
| Python | 3.11.8 (pyenv) | OK |
| Node.js | v22.22.2 (nvm) | OK |
| npm | 10.9.7 | OK |
| pip | 25.0.1 | OK |
| FFmpeg | 8.1 (Homebrew) | OK |
| Docker | 未確認 | 後で確認 |

### Ruff Lint エラー詳細 (Phase 2 で修正)
| ファイル | エラー | 種別 |
|---------|--------|------|
| `app/api/routes.py:11` | `AnalysisNotFoundError` unused import | F401 (auto-fix) |
| `app/models/face_mesh.py:101` | Argument `R` should be lowercase | N803 |
| `app/models/smpl.py:54` | `torch` unused import | F401 (auto-fix) |
| `app/scripts/download_models.py:8` | `Path` unused import | F401 (auto-fix) |
| `app/services/ideal_comparator.py:7` | `numpy` unused import | F401 (auto-fix) |
| `app/services/overlay_renderer.py:10` | `TARGET_JOINTS` unused import | F401 (auto-fix) |

## Resources
- API 仕様書: `docs/api-spec.md`
- SMPL 関節マッピング: `CLAUDE.md` 内テーブル
- Docker 構成: `docker-compose.yml` (4 サービス)
- CI/CD: `.github/workflows/ci.yml`

---
*Update this file after every 2 view/browser/search operations*
