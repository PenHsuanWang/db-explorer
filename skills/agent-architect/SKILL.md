---
name: agent-architect
description: A meta-skill for designing, scaffolding, and implementing new Claude Code Agents/Skills.
argument-hint: [new-agent-name] [goal]
---

# Agent Architect

## Goal
To construct robust, production-grade AI agents by strictly following the **Plan-and-Solve** (SPARC) methodology.

## Workflow

### 1. Specification (The "Plan")
1.  **Ask:** Clarify inputs, outputs, and constraints.
2.  **Draft:** Create `[agent-name]/SPEC.md` using `templates/SPEC_TEMPLATE.md`.
3.  **Review:** Wait for user approval.

### 2. Architecture (The "Skeleton")
1.  **Scaffold:** Create directories (`scripts`, `references`, `tests`).
2.  **Generate:** Create `[agent-name]/SKILL.md` using `templates/SKILL_TEMPLATE.md`.
3.  **Code Quality Setup:** For Python projects, set up code quality tools:
    *   Create `pyproject.toml` using `templates/pyproject.toml.template`
    *   Create `.pre-commit-config.yaml` using `templates/.pre-commit-config.yaml`
    *   Create `tests/conftest.py` using `templates/conftest.py`

### 3. Implementation (The "Solve")
1.  **Scripting:** Write complex logic in `[agent-name]/scripts/` (Python/Bash).
2.  **Refinement:** Update `SKILL.md` to use these scripts.
3.  **Code Quality:** For Python implementations:
    *   **Type Hints:** Ensure all public functions have complete type annotations (PEP 484, 585, 604)
    *   **Docstrings:** Add Google-style docstrings to all public APIs (PEP 257)
    *   **Error Handling:** Implement custom exception hierarchy and use context managers

### 4. Verification
1.  **Format:** For Python code, run `black` and `isort` on all source files
2.  **Type Check:** Run `mypy --strict` and fix type errors
3.  **Lint:** Check YAML frontmatter and run `ruff check` for Python
4.  **Test:** Run `pytest` with 80%+ coverage target
5.  **Security:** Run `safety check` on Python dependencies
6.  **Dry Run:** Perform a final validation of the agent

## Code Quality Standards

For Python projects, follow comprehensive coding standards:
- **Reference:** See Python coding standards for detailed guidelines
- **Formatting:** Black (100 char line length), isort
- **Type Checking:** Mypy strict mode with complete type hints
- **Testing:** Pytest with 80%+ coverage, fixtures, parametrized tests
- **Security:** No secrets in code, parameterized queries, security scanning

## Design Patterns

Apply appropriate design patterns to maintain clean architecture:
- **Creational:** Factory Pattern (for connector creation), Builder Pattern (for configuration)
- **Structural:** Adapter Pattern (database adapters), Decorator Pattern (tracing, metrics)
- **Behavioral:** Strategy Pattern (query execution), Iterator Pattern (streaming), Observer Pattern (events)

## Tools & Scripts

*   `scripts/lint_check.sh`: Run all code quality checks (black, isort, mypy, ruff, safety)
*   `scripts/run_tests.sh`: Run pytest with coverage reporting and various options

## Templates

*   `templates/SPEC_TEMPLATE.md`: Specification template
*   `templates/SKILL_TEMPLATE.md`: Skill documentation template
*   `templates/pyproject.toml.template`: Python project configuration
*   `templates/.pre-commit-config.yaml`: Pre-commit hooks configuration
*   `templates/test_template.py`: Pytest test examples
*   `templates/conftest.py`: Pytest configuration and shared fixtures

