---
name: ski-frontend-change
description: Use when changing Next.js pages, React components, hooks, styles, API client code, or frontend tests in the ski-analyzer repository. Do not use for backend-only work.
---

# Ski Frontend Change

Start with `CLAUDE.md`, the repo root `AGENTS.md`, and `frontend/AGENTS.override.md`.

## Workflow

1. Inspect the page, component, hook, and type files touched by the request.
2. Preserve the upload-to-analysis flow and do not assume backend response shapes.
3. If UI depends on API or analysis data, verify `src/types/analysis.ts` and `src/utils/api.ts` against backend schemas and routes.
4. Keep confidence labels and "reference value" behavior aligned with the single-camera accuracy constraints in `CLAUDE.md`.

## Validation

- Run `npm run lint` in `frontend/`.
- Run `npx tsc --noEmit` in `frontend/`.
- Run targeted Jest tests first, then `npm test -- --runInBand` when the change is broad.
