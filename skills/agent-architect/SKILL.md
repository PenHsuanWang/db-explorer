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

### 3. Implementation (The "Solve")
1.  **Scripting:** Write complex logic in `[agent-name]/scripts/` (Python/Bash).
2.  **Refinement:** Update `SKILL.md` to use these scripts.

### 4. Verification
1.  **Lint:** Check YAML frontmatter.
2.  **Test:** Perform a dry run.
