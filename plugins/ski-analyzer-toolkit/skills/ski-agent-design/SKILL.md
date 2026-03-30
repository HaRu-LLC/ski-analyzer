---
name: ski-toolkit-agent-design
description: Use when designing or updating app-side agent boundaries, provider selection, structured outputs, review flows, guardrails, or durable agent docs in the ski-analyzer repository through the installed Ski Analyzer Toolkit plugin.
---

# Ski Agent Design

Start with `docs/codex-agent-ops.md`, `docs/app-agent-architecture.md`, and the repo root `AGENTS.md`.

## Workflow

1. Keep deterministic video analysis steps as code, not agents.
2. Limit agents to narrative generation, review, or other clearly scoped language tasks.
3. Preserve the public `coaching` shape unless the change explicitly includes API and frontend updates.
4. Prefer structured output, explicit schemas, and review or fallback paths over freeform text generation.

## Validation

- Confirm provider selection and fallback behavior in backend tests.
- Confirm public API compatibility in backend schemas and frontend types.
- Update durable docs when agent boundaries or guardrails change.
