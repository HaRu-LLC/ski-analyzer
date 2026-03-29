# 🎿 Ski Analyzer - スキーシミュレータ動画解析アプリ

室内スキーシミュレータの滑走フォームをAI動画解析で可視化し、スキー技術の改善を支援するWebアプリケーションです。

## 特徴

- **3D姿勢推定**: SMPLベースのHMRモデルで関節の3D位置・回転を推定
- **コマ送り再生**: フレーム単位での詳細なフォーム確認
- **関節角度分析**: 膝・股関節・胸郭・肩・頭・肘・手首の角度を数値化
- **AIコーチング**: Claude APIによる日本語フォーム改善アドバイス
- **理想フォーム比較**: 模範フォームとの差分を可視化

## クイックスタート

```bash
# リポジトリをクローン
git clone https://github.com/your-org/ski-analyzer.git
cd ski-analyzer

# 環境変数を設定
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定

# Docker で起動
docker-compose up -d

# ブラウザで開く
open http://localhost:3000
```

## 開発環境セットアップ

### 前提条件

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- FFmpeg
- (GPU推論する場合) NVIDIA GPU + CUDA 12+

### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

### バックエンド

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.scripts.download_models  # 初回のみ
uvicorn app.main:app --reload --port 8000
```

## 撮影ガイド

最適な解析結果を得るために:

1. **カメラ**: 正面1台、三脚固定
2. **高さ**: 股関節〜胸の中間
3. **距離**: 全身が画面の60〜70%を占める
4. **解像度**: 1080p以上、60fps以上
5. **服装**: 半袖・短パンなど体のラインが分かる服装
6. **動画長**: 1分以内

## ライセンス

MIT License
