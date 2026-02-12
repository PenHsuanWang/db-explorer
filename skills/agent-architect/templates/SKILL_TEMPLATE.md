---
name: [agent-id-kebab-case]
description: [Short description < 200 chars]
argument-hint: [args]
---

# [Agent Name]

## Goal
[High-level objective]

## Workflow
1.  **[Step 1]:** [Instruction]
2.  **[Step 2]:** [Instruction]

## Tools
*   `scripts/[script_name].py`: [Description]

## Code Quality
- **Formatting**: Black (line length 100), isort
- **Linting**: Ruff
- **Type Checking**: Mypy (strict mode)
- **Testing**: Pytest with 80%+ coverage

## Scripts
*   `scripts/lint_check.sh`: Run all code quality checks
*   `scripts/run_tests.sh`: Run test suite with coverage

## References
See `references/` for detailed documentation.
