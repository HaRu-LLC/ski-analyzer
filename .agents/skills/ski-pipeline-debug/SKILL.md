---
name: ski-pipeline-debug
description: Use when debugging issues that span upload, status polling, result retrieval, video processing, pose estimation, coaching generation, rendering, or frontend analysis flow in the ski-analyzer repository.
---

# Ski Pipeline Debug

Start with `CLAUDE.md`, the repo root `AGENTS.md`, and the nearest backend or frontend override.

## Workflow

1. Map the symptom to a stage: upload, frame extraction, pose estimation, angle calculation, coaching, report or overlay rendering, API delivery, or frontend rendering.
2. Trace the contract at each boundary before editing: route, schema, service output, frontend type, and UI usage.
3. Distinguish deterministic pipeline bugs from agent or provider bugs before changing code.
4. Prefer `USE_MOCK=true` when isolating non-model bugs in the backend pipeline.
5. Fix the narrowest broken stage first, then re-check adjacent stages.

## Validation

- Run the smallest backend and frontend checks that exercise the failing boundary.
- If a response shape changed, validate both backend tests and frontend type or UI checks.
- If the issue affects generated artifacts, verify the related service tests before broadening the fix.
