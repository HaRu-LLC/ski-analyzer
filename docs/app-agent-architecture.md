# App Agent Architecture

## v1 の境界

agent を使うのは coaching narrative の生成と review のみとする。以下は決定論的な code path のまま維持する。

- upload / validation
- frame extraction
- pose estimation
- angle calculation
- ideal comparison
- overlay rendering
- report assembly

## Provider 設計

- `CoachingGenerator` は facade
- `LLM_PROVIDER=anthropic|openai` で provider を切り替える
- Anthropic は既存互換 path を維持する
- OpenAI は structured output + review path を使う

## OpenAI path

1. `coaching-writer` が入力データから coaching JSON を生成する
2. `coaching-reviewer` が unsupported claim、低信頼軸の断定、部位取り違えを確認する
3. review で reject された場合は default coaching に落とす
4. 内部メタデータは `agent_trace.json` に保存し、public API には混ぜない

## Public contract

- `/api/analysis/{id}/result` の `coaching` shape は維持する
- frontend の `CoachingAdvice` 型は変更しない
- trace は internal artifact として保存する
