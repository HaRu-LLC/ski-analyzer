---
name: ski-review-fix-loop
description: Use when asked to review changes, fix the findings, and re-review the result in the ski-analyzer repository.
---

# Ski Review Fix Loop

Start with `CLAUDE.md`, the repo root `AGENTS.md`, `code_review.md`, and the nearest backend or frontend override for touched files.

## Workflow

1. Define the review scope first: current diff, target files, and adjacent contracts that could regress.
2. Run an initial review in findings-first format. Prioritize regressions, API contract breaks, async or heavy-path issues, missing validation, and doc or ops drift.
3. Only fix findings you can support concretely from code or tests. Keep fixes narrow and avoid unrelated refactors while the loop is active.
4. After each fix pass, run the smallest validation that exercises the touched layer and any contract boundary you changed.
5. Re-review the updated diff, including the new code you wrote, for unresolved findings and fix-induced regressions.
6. Cap the loop at 5 iterations by default to avoid unbounded churn. If the user explicitly specifies an iteration count, use that count instead.
7. Repeat the fix and re-review cycle while there are still material findings that are in scope, can be resolved safely in the current session, and the iteration budget is not exhausted.
8. Stop when the latest re-review finds no material issues, when the iteration budget is exhausted, or when remaining risks require product direction, external access, or a broader refactor than the task allows.

## Output

- For each review pass, report findings before summaries and include file and line references.
- If the first pass is clean, say so explicitly and report only residual risks or missing validation.
- In the final handoff, separate: fixed findings, remaining risks, validation run, and whether the loop stopped because it was clean or because it hit the iteration cap.

## Validation

- Run at least one concrete check for the changed layer before closing the loop.
- If backend and frontend contracts were both touched, validate both sides or state the gap explicitly.
- Do not claim the re-review is clean if required checks were skipped; call out the residual risk instead.
