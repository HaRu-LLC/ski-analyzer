# AGENTS.md

このリポジトリで作業する前に、まず `CLAUDE.md` を読むこと。プロジェクト仕様、アーキテクチャ、開発コマンド、環境変数、解析パイプライン、精度制約、コーディング規約は `CLAUDE.md` を正とする。このファイルと `CLAUDE.md` が矛盾する場合は `CLAUDE.md` を優先する。

## 参照順

1. `CLAUDE.md`
2. 現在の作業ディレクトリに最も近い `AGENTS.override.md` または `AGENTS.md`
3. 変更対象に近い設定ファイル
   - `backend/pyproject.toml`
   - `frontend/package.json`
   - `docker-compose.yml`
   - `.github/workflows/ci.yml`
4. `README.md`
5. `docs/api-spec.md`
6. `docs/codex-agent-ops.md`
7. `docs/app-agent-architecture.md`
8. `code_review.md`

## リポジトリ概要

- `frontend/`: Next.js 14 + TypeScript + Tailwind CSS + Jest
- `backend/`: FastAPI + Python 3.11 + Ruff + Pytest
- `infrastructure/`: Docker / Nginx / GPU 関連設定
- `docs/`: API 仕様
- `.agents/skills/`: repo 専用の Codex skills
- `.agents/plugins/marketplace.json`: repo ローカル plugin カタログ
- `docs/codex-agent-ops.md`: Codex / agent 運用方針
- `docs/app-agent-architecture.md`: app 内 agent 境界と guardrails

## 作業ルール

- 変更は対象サブシステムに閉じる。フロントエンドとバックエンドをまたぐ変更は API 契約の整合を確認する。
- 実装方針、環境変数、解析パイプライン、精度制約は `CLAUDE.md` に従う。
- API 仕様やレスポンス shape を変える場合は、`backend/app/schemas/`、`frontend/src/types/`、`frontend/src/utils/api.ts`、`docs/api-spec.md` の整合を確認する。
- 秘密情報は `.env` で扱い、キーや認証情報をコミットしない。
- ローカル起動やサービス構成の確認が必要な場合は `docker-compose.yml` と `CLAUDE.md` の開発コマンドを参照する。
- repo 内の繰り返し作業は `.agents/skills/` の skill を優先して再利用し、広く配布したい場合だけ plugin 化する。

## Done の定義

- 変更したレイヤーに対応する検証を少なくとも 1 つ実行し、結果を共有する。
- 影響範囲が広い変更では、近接レイヤーの契約不整合がないことを確認する。
- レビュー時は `code_review.md` の方針に従う。

## 補足

- この `AGENTS.md` は入口用の要約であり、詳細仕様を再定義しない。
- より具体的な制約が必要な場合は `backend/AGENTS.override.md` と `frontend/AGENTS.override.md` を優先する。
- 判断に迷う場合は、常に `CLAUDE.md` の内容に寄せる。
