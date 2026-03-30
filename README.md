# Ski Analyzer

室内スキーシミュレータの滑走動画を解析し、関節角度、理想フォーム比較、AI コーチングを返すアプリケーションです。

## 現在の推奨実行モード

ローカル確認は `USE_MOCK=true` のデモモードを前提にしています。
このモードでは upload -> status polling -> result 表示 -> CSV/PDF ダウンロードまでを安定して確認できます。

- 3D ポーズ推定は mock データで代替
- `result.json`, `angles.csv`, `agent_trace.json`, `report.pdf` を生成
- `overlay.mp4` は入力動画とローカル FFmpeg/OpenCV の状態に依存して生成されます

## Quick Start

### Docker

```bash
cp .env.example .env
docker-compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

GPU / real-mode 準備用 override:

```bash
cp .env.example .env
sed -i '' 's/USE_MOCK=true/USE_MOCK=false/' .env
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

この override は GPU 対応コンテナと `USE_MOCK=false` を有効化します。
ただし現時点では pose estimator は必要モデル不足や未統合 runtime を明示的に fail-fast する段階で、実 HMR 推論そのものは未完了です。

### ローカル起動

Backend:

```bash
cp .env.example .env
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

モデル配置確認:

```bash
cd backend
.venv/bin/python -m app.scripts.download_models --check
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## 検証コマンド

Backend:

```bash
cd backend
.venv/bin/ruff check app/
.venv/bin/python -m ruff format --check app/
.venv/bin/pytest -q
```

Frontend:

```bash
cd frontend
npm run lint
npx tsc --noEmit
npm test -- --runInBand
```

## 実装上の注意

- 現在の API 実装は FastAPI `BackgroundTasks` ベースで、Celery worker は標準構成に含めていません。
- `download/video` と `download/report` は成果物が生成できた場合のみ有効です。
- `USE_MOCK=false` では必要モデル不足や未統合 runtime を明示的にエラーにします。暗黙に mock へフォールバックはしません。
- 実 HMR モデル統合と GPU 常設運用は後続フェーズの扱いです。

## 撮影ガイド

1. 正面から三脚で固定撮影
2. 全身が画面の 60〜70% に収まる距離
3. 1080p 以上、60fps 以上
4. 体のラインが見える服装
5. 1 分以内の動画

## License

MIT
