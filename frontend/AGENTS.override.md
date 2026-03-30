# Frontend Override

このディレクトリ配下では Next.js / TypeScript 側の規約を優先する。

## Focus

- 主対象は `src/app/`、`src/components/`、`src/hooks/`、`src/types/`、`src/utils/`
- API 契約に触れる場合は `src/types/analysis.ts` と `src/utils/api.ts` を起点に確認する
- 解析画面の変更では `src/app/analyze/[id]/page.tsx` と関連 component の整合を保つ

## Validation

- 基本: `npm run lint`
- 型確認: `npx tsc --noEmit`
- テスト: `npm test -- --runInBand`

## Guardrails

- バックエンド API shape を仮定で変えない
- UI 表示の精度ラベルや参考値の扱いは `CLAUDE.md` の精度制約に従う
- 単なる見た目変更でも、アップロードから結果表示までの導線を壊さない
