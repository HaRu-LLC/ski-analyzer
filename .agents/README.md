# .agents README

このディレクトリは、この repo で Codex を使うための repo-local assets をまとめる場所です。短期の作業指示は chat に、繰り返し使う workflow は `skills/` に、配布単位は `plugins/marketplace.json` に寄せます。

## 構成

- `.codex/agents/`
  - repo 専用の custom subagents
  - `pipeline_mapper`、`coaching_reviewer`、`docs_researcher`、`browser_debugger` を定義している
  - 並列 delegation で使う役割を固定する場所
- `skills/`
  - repo 内でそのまま使う Codex skills
  - backend / frontend / pipeline / agent design / agent evals のように責務ごとに分割している
- `plugins/marketplace.json`
  - local plugin marketplace の入口
  - `plugins/ski-analyzer-toolkit/` を install 可能な plugin として公開する

## Skills の内容

- `ski-backend-change`
  - FastAPI / Python / schema / route / service / backend test の変更用
  - API shape を変えるときは frontend 型と docs の整合も見る
- `ski-frontend-change`
  - Next.js / component / hook / type / API client / frontend test の変更用
  - upload から analyze までの導線維持を重視する
- `ski-pipeline-debug`
  - upload, frame extraction, pose estimation, angle calculation, coaching, report, API, UI の跨り障害切り分け用
  - deterministic pipeline の問題か、agent/provider の問題かを先に分ける
- `ski-agent-design`
  - app-side agent の境界、structured output、review flow、guardrails、provider 切替の設計用
  - 動画解析本体は agent 化せず、coaching narrative と review に限定する前提
- `ski-agent-evals`
  - unsupported claim、low-confidence overstatement、fallback、trace grading、fixture 回帰の設計用
  - 出力品質より先に schema compliance と fallback correctness を確認する

## 良い使い方

- まず `AGENTS.md`、必要なら `backend/AGENTS.override.md` か `frontend/AGENTS.override.md` を読む
- 並列で役割分担したいときは built-in agent だけで済むかを先に考える
  - 実装担当は built-in `worker`
  - 読み中心の探索は built-in `explorer`
  - repo 固有の役割が必要なときだけ `.codex/agents/` の custom subagent を使う
- task が明確なら skill 名を明示して呼ぶ
  - 例: `Use ski-backend-change to update the coaching provider`
  - 例: `Use ski-pipeline-debug to investigate why result.json is missing`
- repo 固有 subagent の使い分け
  - `pipeline_mapper`: 実行経路の把握、影響範囲の切り分け、バグ調査の前段
  - `coaching_reviewer`: coaching path の review、guardrail/fallback/schema 監査
  - `docs_researcher`: OpenAI / MCP / Codex / framework の一次情報確認
  - `browser_debugger`: UI 再現、console/network 証拠取得、integration bug 切り分け
- task が複合的でも、最初の主戦場に対応する skill を 1 つ選ぶ
  - backend 変更が主なら `ski-backend-change`
  - 設計レビューが主なら `ski-agent-design`
  - 評価戦略や failure mode 整理が主なら `ski-agent-evals`
- API shape を変える場合は skill 任せにせず、`backend/app/schemas/`、`frontend/src/types/analysis.ts`、`frontend/src/utils/api.ts`、`docs/api-spec.md` を必ずセットで確認する
- skill は durable workflow の再利用に使い、単発の細かい事情はその都度 chat で渡す

## 避けたい使い方

- 1つの skill に複数の責務を詰め込む
- custom subagent を skill の代わりに大量作成する
- backend と frontend の両方を大きく触るのに、契約確認なしで片側だけ進める
- freeform prompt だけで agent 出力を信用し、schema や fallback を省略する
- plugin を先に増やし、repo-local skill を固めないまま配布し始める

## Plugin の位置づけ

- `skills/` はこの repo の中で直接使う作業単位
- `plugins/ski-analyzer-toolkit/` は、それらを install 可能な配布物にしたもの
- まず repo-local skill で運用を安定させ、複数 repo や複数メンバーで再利用したくなった段階で plugin を使う

## 更新ルール

- 新しい繰り返し作業が増えたら、まず `skills/` に追加する
- 新しい「並列で使い回す役」が必要になったときだけ `.codex/agents/` に custom subagent を追加する
- skill の境界や運用方針が変わったら、この README と `docs/codex-agent-ops.md` を一緒に更新する
- app-side agent の境界が変わったら `docs/app-agent-architecture.md` も更新する
