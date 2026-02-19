## Summary

<!-- One or two sentences. Answer: what changed and why? Do not restate the diff. -->

Closes #

---

## Type of Change

Select exactly one. If multiple types apply, consider splitting this PR.

- [ ] feat — new feature (non-breaking)
- [ ] fix — bug fix (non-breaking)
- [ ] refactor — code restructuring, no functional change
- [ ] chore — tooling, dependencies, CI configuration
- [ ] docs — documentation only
- [ ] breaking — modifies `DatabasePort` interface, `CleaningEngine` contract, or FastAPI endpoint schema

---

## Affected Layers

Select all that apply. This helps reviewers scope their focus to the correct hexagonal layer.

- [ ] Domain (`backend/src/core/domain`)
- [ ] Ports (`backend/src/core/ports`)
- [ ] Application / CleaningEngine (`backend/src/application`)
- [ ] Adapters — connector(s) affected: ___________
- [ ] API layer (`backend/src/main.py` / routers)
- [ ] Frontend (`web-ui/src`)

---

## Implementation Notes

<!--
Explain *why* this approach was chosen over alternatives.
- If this is a breaking change: describe the migration path for callers.
- If this adds a new connector adapter: confirm read-only enforcement and UniversalDataType normalization are implemented.
- Leave N/A only if genuinely not applicable.
-->

---

## Validation

### Automated Checks

All boxes must be checked before requesting review. Do not mark a box unless the command has actually been run and passed.

- [ ] `cd backend && pytest tests/` — all tests pass
- [ ] `cd backend && ruff check src/ tests/` — zero lint errors
- [ ] `cd backend && mypy --strict src/` — zero type errors
- [ ] `cd web-ui && npm run lint` — zero ESLint errors
- [ ] `cd web-ui && npm run test` — Vitest suite passes

### Manual Verification Steps

Provide at minimum two concrete, executable steps a reviewer can follow to verify the change.

1.
2.
3.

### Read-Only Safety

Required when `adapters/`, `ports/`, or `application/` is modified. Skip this section only for `docs` and `chore` changes that do not touch those layers.

- [ ] No `INSERT` / `UPDATE` / `DELETE` / DDL statement is reachable through the modified code path.
- [ ] `ReadOnlyViolationError` is raised before any write-keyword SQL reaches the database driver.

---

## Pre-Submission Checklist

- [ ] Self-review completed — no debug logs, no commented-out code, no hardcoded secrets or real DSNs.
- [ ] New public functions and methods have reStructuredText (reST) docstrings and complete type annotations (PEP 484).
- [ ] `CLAUDE.md` or relevant architecture reference documents updated if contracts or data flow changed.
- [ ] PR title follows Conventional Commits: `<type>(<scope>): <subject>` — e.g., `feat(adapter-oracle): add streaming cursor support`.