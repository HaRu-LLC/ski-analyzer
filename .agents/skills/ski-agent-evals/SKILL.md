---
name: ski-agent-evals
description: Use when adding or updating evaluation, trace grading, fallback checks, unsupported-claim detection, or regression fixtures for app-side agent behavior in the ski-analyzer repository.
---

# Ski Agent Evals

Start with `docs/codex-agent-ops.md`, `docs/app-agent-architecture.md`, and the nearest backend tests.

## Workflow

1. Evaluate schema compliance before qualitative output quality.
2. Add fixture cases for unsupported claims, low-confidence overstatement, fallback activation, and provider selection.
3. Keep trace artifacts internal and test them as internal outputs, not public API fields.
4. Treat review rejection and fallback as success paths that must be covered by tests.

## Validation

- Run targeted backend tests for provider selection and coaching generation.
- Verify `result.json` stays compatible while internal trace artifacts can change.
- Prefer deterministic fixtures over subjective prompt snapshots.
