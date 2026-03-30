---
name: ski-backend-change
description: Use when changing backend FastAPI, Python services, schemas, routes, config, or tests in the ski-analyzer repository. Do not use for frontend-only work.
---

# Ski Backend Change

Start with `CLAUDE.md`, the repo root `AGENTS.md`, and `backend/AGENTS.override.md`.

## Workflow

1. Inspect the affected files in `backend/app/` and the nearest tests in `backend/tests/`.
2. Keep the change scoped to the backend unless the API contract changes.
3. If request or response shapes change, verify `backend/app/schemas/`, `frontend/src/types/analysis.ts`, `frontend/src/utils/api.ts`, and `docs/api-spec.md`.
4. Prefer targeted fixes over broad refactors in the analysis pipeline.

## Validation

- Run `ruff check app/` in `backend/`.
- Run `ruff format --check app/` in `backend/`.
- Run targeted `pytest` first, then `pytest tests/ -v` when the change is broad.
- For pipeline checks that do not need real inference, prefer `USE_MOCK=true`.
