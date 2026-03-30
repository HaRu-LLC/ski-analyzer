# Ski Simulator Video Analysis App

## プロジェクト概要

室内スキーシミュレータの滑走動画をAIで解析し、3D姿勢推定・関節角度算出・AIコーチングを提供するWebアプリケーション。

## アーキテクチャ

```
[ブラウザ] ──HTTP/WS──▶ [FastAPI Backend] ──GPU推論──▶ [HMR Engine]
                              │                            │
                              ├── FFmpeg (フレーム抽出)      ├── SMPL 3Dポーズ推定
                              ├── LLM Provider (コーチング)  └── MediaPipe (顔補完)
                              └── S3 (動画/結果保存)
```

### フロントエンド: `frontend/`
- **フレームワーク**: Next.js 14 (App Router) + TypeScript
- **3D描画**: Three.js (スケルトン重畳)
- **グラフ**: Recharts (関節角度時系列)
- **スタイル**: Tailwind CSS
- **状態管理**: Zustand

### バックエンド: `backend/`
- **フレームワーク**: Python 3.11 + FastAPI
- **姿勢推定**: SMPLベースHMR (PyTorch)
- **顔補完**: MediaPipe Face Mesh
- **動画処理**: FFmpeg (subprocess)
- **AIコーチング**: Anthropic Claude API または OpenAI structured agent
- **非同期タスク**: Celery + Redis

## ディレクトリ構成

```
ski-analyzer/
├── frontend/                 # Next.js 14 (App Router)
│   ├── src/
│   │   ├── app/              # ページ: page.tsx (トップ), analyze/[id]/page.tsx (結果)
│   │   ├── components/       # VideoUploader, VideoPlayer, SkeletonOverlay, AnglePanel, AngleGraph, CoachingPanel 等
│   │   ├── hooks/            # useVideoPlayer, useAnalysis, useKeyboardShortcuts
│   │   ├── types/            # analysis.ts
│   │   └── utils/            # api.ts (APIクライアント)
│   ├── Dockerfile
│   └── package.json
│
├── backend/                  # Python 3.11 + FastAPI
│   ├── app/
│   │   ├── main.py           # エントリポイント
│   │   ├── api/              # routes.py, deps.py
│   │   ├── schemas/          # upload.py, analysis.py
│   │   ├── services/         # video_processor, pose_estimator, angle_calculator, coaching_generator 等
│   │   ├── models/           # smpl.py, face_mesh.py
│   │   └── scripts/          # download_models.py
│   ├── tests/                # test_services.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── docs/                     # api-spec.md
├── infrastructure/           # Dockerfile.gpu, nginx.conf
└── .github/workflows/        # ci.yml
```

## 開発コマンド

```bash
# ローカル開発環境の起動
docker-compose up -d

# フロントエンド
cd frontend && npm run dev        # http://localhost:3000

# バックエンド
cd backend && uvicorn app.main:app --reload --port 8000

# テスト
cd backend && pytest
cd frontend && npm test

# リント/フォーマット
cd backend && ruff check app/ && ruff format --check app/
cd frontend && npm run lint

# モデルダウンロード（初回のみ）
cd backend && python -m app.scripts.download_models
```

## API エンドポイント

| Method | Path | 説明 |
|--------|------|------|
| POST | `/api/upload` | 動画アップロード |
| GET | `/api/analysis/{id}/status` | 解析状況確認 |
| GET | `/api/analysis/{id}/result` | 解析結果取得 |
| GET | `/api/analysis/{id}/frames/{frame}` | フレーム別データ取得 |
| GET | `/api/download/{id}/video` | スケルトン重畳動画DL |
| GET | `/api/download/{id}/report` | PDFレポートDL |
| GET | `/api/download/{id}/csv` | CSV数値データDL |

## 環境変数

```
# バックエンド
LLM_PROVIDER=anthropic     # anthropic / openai
ANTHROPIC_API_KEY=         # Claude API キー
OPENAI_API_KEY=            # OpenAI API キー
OPENAI_AGENT_MODEL=gpt-5.2
OPENAI_REASONING_EFFORT=low
STORAGE_PATH=/data/uploads # 動画保存パス
MODEL_PATH=/data/models    # HMRモデルパス
REDIS_URL=redis://redis:6379/0
MAX_VIDEO_DURATION=60      # 最大動画長（秒）
MAX_FILE_SIZE=524288000    # 最大ファイルサイズ（500MB）
AUTO_DELETE_HOURS=24       # 自動削除時間

# フロントエンド
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## コーディング規約

- Python: ruff (formatter + linter), type hints必須, docstring必須
- TypeScript: ESLint + Prettier, strict mode
- コミットメッセージ: Conventional Commits (feat:, fix:, docs: 等)
- ブランチ戦略: main → develop → feature/xxx

## 解析パイプライン詳細

```
1. アップロード → 動画バリデーション（解像度/fps/長さ）
2. FFmpeg → フレーム抽出（全フレーム JPEG）
3. HMR推論 → 各フレームのSMPLパラメータ（shape β, pose θ, camera）
   - pose θ: 24関節 × 3 (axis-angle) = 72次元
   - shape β: 10次元
4. MediaPipe Face Mesh → 頭部回転補完（468ランドマーク → 3D回転）
5. 関節角度算出 → axis-angle → Euler角変換
   - 対象: 膝, 股関節, 胸郭(Spine1-3), 肩, 頭, 肘, 手首
6. 理想フォーム比較 → 関節角度の差分計算
7. LLM Provider → コーチング生成
   - anthropic: 既存互換の単発生成
   - openai: structured output + review + internal trace
8. 結果保存 → JSON + agent_trace.json + スケルトン重畳動画レンダリング
```

## SMPL関節マッピング

| Index | Joint | 日本語 | 解析対象 |
|-------|-------|--------|----------|
| 0 | Pelvis | 骨盤 | 基準点 |
| 1 | L_Hip | 左股関節 | ✅ |
| 2 | R_Hip | 右股関節 | ✅ |
| 3 | Spine1 | 脊椎下部 | ✅ 胸郭 |
| 4 | L_Knee | 左膝 | ✅ |
| 5 | R_Knee | 右膝 | ✅ |
| 6 | Spine2 | 脊椎中部 | ✅ 胸郭 |
| 9 | Spine3 | 脊椎上部 | ✅ 胸郭 |
| 12 | Neck | 首 | ✅ 頭 |
| 13 | L_Collar | 左鎖骨 | - |
| 14 | R_Collar | 右鎖骨 | - |
| 15 | Head | 頭 | ✅ |
| 16 | L_Shoulder | 左肩 | ✅ |
| 17 | R_Shoulder | 右肩 | ✅ |
| 18 | L_Elbow | 左肘 | ✅ |
| 19 | R_Elbow | 右肘 | ✅ |
| 20 | L_Wrist | 左手首 | ✅ |
| 21 | R_Wrist | 右手首 | ✅ |

## 正面カメラ1台の精度制約

正面カメラ1台では奥行き方向（Z軸）の回転推定精度が低い。
以下の方針でUIに反映する:

- **高精度（左右方向の位置・回転）**: 数値を確信度「高」で表示
- **中精度（屈曲角度）**: 数値を確信度「中」で表示
- **低精度（前傾・回旋）**: 「参考値」ラベルを付与、定性表現を使用

## 注意事項

- GPU推論は重いため、ローカル開発ではCPUモードまたはモック推論を使用可能
- `backend/app/services/pose_estimator.py` に `USE_MOCK=true` でダミーデータ返却モードあり
- 動画は24時間後に自動削除（cron or Celery beat）
- ログイン不要のため、セッションIDベースで解析結果を管理
