---
name: pr-guide
description: A skill for authoring high-quality, fast-iteration Pull Request descriptions for the db-explorer project. Generates a structured PR description following the Agile-Lean template.
argument-hint: [branch-name] [summary-of-change]
---

# PR Guide — Fast-Iteration Pull Request Authoring

## Goal

To produce a well-structured, reviewer-friendly Pull Request description that minimizes review cycle time while preserving traceability and quality accountability. This skill targets the **db-explorer** project's fast-iteration workflow (Python 3.12 / FastAPI / React / Hexagonal Architecture).

---

## When to Invoke

Run this skill whenever you are about to open a PR and want Claude to draft or review the PR description. It is especially useful when:

- The change touches the `DatabasePort` interface or any connector adapter.
- The change modifies the `CleaningEngine` data flow.
- The change crosses both `backend/` and `web-ui/` layers.
- You want to ensure CI gates (lint, type-check, tests) are explicitly declared as passed.

---

## Workflow

### 1. Gather Context

Before generating the description, collect:

1. **Ticket / Issue number** — from the issue tracker (e.g., `#42` for GitHub, `PROJ-123` for Jira/Bitbucket).
2. **Type of change** — one of: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`.
3. **Affected layers** — select all that apply:
   - `backend/src/core/domain`
   - `backend/src/core/ports`
   - `backend/src/application`
   - `backend/src/adapters`
   - `web-ui/src`
4. **Test evidence** — confirm which of the following apply:
   - `pytest` suite passed locally (`cd backend && pytest tests/`)
   - `ruff check` passed (`cd backend && ruff check src/ tests/`)
   - `mypy --strict` passed
   - `npm run lint` passed (`cd web-ui && npm run lint`)
   - `npm run test` (Vitest) passed
5. **Breaking change flag** — does this PR modify `DatabasePort` interface, the `CleaningEngine` contract, or any public FastAPI endpoint schema?

### 2. Generate the PR Description

Use the template in the **Template** section below. Fill every mandatory field; mark optional fields as `N/A` only when genuinely not applicable.

### 3. Self-Review Before Submitting

Run through the **Pre-Submission Checklist** embedded in the template. Every unchecked item must be resolved or explicitly justified in the "Implementation Notes" section.

---

## Template

Copy the following block into your Pull Request description.

---

## Summary

One or two sentences. Answer: what changed and why?

Closes [issue-reference]

## Type of Change

- [ ] feat — new feature (non-breaking)
- [ ] fix — bug fix (non-breaking)
- [ ] refactor — code restructuring, no functional change
- [ ] chore — tooling, dependencies, CI
- [ ] docs — documentation only
- [ ] breaking — modifies DatabasePort interface, CleaningEngine contract, or FastAPI schema

## Affected Layers

- [ ] Domain (backend/src/core/domain)
- [ ] Ports (backend/src/core/ports)
- [ ] Application / CleaningEngine (backend/src/application)
- [ ] Adapters — specify connector(s): ___________
- [ ] API layer (backend/src/main.py / routers)
- [ ] Frontend (web-ui/src)

## Implementation Notes

Explain why this approach was chosen over alternatives.
If a breaking change, describe the migration path.
If a new connector adapter: confirm read-only enforcement and UniversalDataType normalization.

## Validation

### Automated Checks (all must pass before merge)

- [ ] cd backend && pytest tests/ — all tests pass
- [ ] cd backend && ruff check src/ tests/ — zero lint errors
- [ ] cd backend && mypy --strict src/ — zero type errors
- [ ] cd web-ui && npm run lint — zero ESLint errors
- [ ] cd web-ui && npm run test — Vitest suite passes

### Manual Verification Steps

1.
2.
3.

### Read-Only Safety (required for any adapter or port change)

- [ ] No INSERT / UPDATE / DELETE / DDL is reachable through the modified code path.
- [ ] ReadOnlyViolationError is raised before any write-keyword SQL reaches the driver.

## Pre-Submission Checklist

- [ ] Self-review completed — no debug logs, no commented-out code, no hardcoded secrets.
- [ ] New public functions have reStructuredText (reST) docstrings and complete type annotations.
- [ ] CLAUDE.md or architecture reference docs updated if contracts changed.
- [ ] PR title follows Conventional Commits format: type(scope): subject

---

## Field Reference

| Field | Mandatory | Guidance |
| :--- | :---: | :--- |
| Summary | Yes | Must state what changed and why. Do not restate the diff. |
| Closes [issue] | Yes | Use platform keywords (Closes, Fixes, Resolves) to auto-link/close the issue. |
| Type of Change | Yes | Select exactly one; if multiple apply, split into separate PRs. |
| Affected Layers | Yes | Helps reviewers scope their focus; hexagonal layer boundaries are strict. |
| Implementation Notes | Yes | Required for breaking type; optional but strongly recommended for all others. |
| Automated Checks | Yes | Every box must be checked. Do not open a PR with failing CI. |
| Manual Verification Steps | Yes | At minimum two concrete steps the reviewer can execute. |
| Read-Only Safety | Conditional | Required whenever adapters/, ports/, or application/ is modified. |
| Pre-Submission Checklist | Yes | All boxes must be checked before requesting review. |

---

## PR Title Convention

Format: type(scope): subject

- type — same values as Type of Change above (feat, fix, refactor, chore, docs, breaking)
- scope — the primary affected module, e.g., adapter-oracle, cleaning-engine, api, web-ui, ci
- subject — imperative mood, lowercase, no period, max 72 characters

Examples:
- feat(adapter-clickhouse): implement execute_query_stream with read-only guard
- fix(cleaning-engine): handle NULL timestamps in UniversalDataType casting
- refactor(api): extract query router into dedicated module
- breaking(ports): add fetch_schema method to DatabasePort interface

---

## Anti-Patterns to Avoid

- Opening a PR with a blank or template-placeholder description.
- Marking CI checkboxes as done before the pipeline has actually run.
- Combining a refactor with a feature in the same PR — split them.
- Attaching secrets, real DSNs, or PII sample data in screenshots or logs.
- Skipping Read-Only Safety boxes for adapter changes.

---

## Scripts Reference

| Script | Purpose |
| :--- | :--- |
| cd backend && pytest tests/ | Run full backend test suite |
| cd backend && ruff check src/ tests/ | Lint backend Python code |
| cd backend && mypy --strict | Type-check backend |
| cd web-ui && npm run lint | Lint frontend TypeScript/React |
| cd web-ui && npm run test | Run Vitest frontend suite |
| docker-compose up -d | Start full stack for manual verification |
| skills/agent-architect/scripts/lint_check.sh | Consolidated backend quality check |
| skills/db-explorer-architect/scripts/lint_backend.sh | Detailed backend lint + test |
| skills/db-explorer-architect/scripts/lint_frontend.sh | Detailed frontend lint + test |
