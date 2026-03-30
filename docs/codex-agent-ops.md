# Codex Agent Ops

## 目的

Codex をこの repo で使うときの durable guidance をまとめる。短期のタスク指示ではなく、繰り返し使う運用原則をここに置く。

## 基本方針

- durable guidance は `AGENTS.md` と override に置く
- repo 固有の繰り返し作業は `.agents/skills/` に切り出す
- skill が安定してから plugin に bundle する
- 外部情報は必要最小限の MCP だけを使い、side effect がある操作は approval を前提にする

## Agent 設計

- agent の責務は狭く保つ
- structured output と明示的な schema を使う
- freeform prompt に非信頼入力を混ぜない
- guardrail は入口と出口の両方でかける
- workflow の問題は trace grading と fixture 回帰で評価する

## Repo への適用

- 決定論的な動画解析パイプラインは agent 化しない
- LLM / agent が扱うのは coaching narrative と review に限定する
- backend / frontend / pipeline debug / agent design / agent evals を別 skill に分ける
- subagent は built-in `worker` / `explorer` を基本とし、repo 固有の役割だけ `.codex/agents/` に custom agent として定義する
- project config では `agents.max_threads = 4`、`agents.max_depth = 1` を基本値とする
