---
name: db-explorer-architect
description: The architecture and scaffolding guide for the Database Explorer project. Provides clear workflows, rules, and tools for adding adapters, implementing features, and ensuring hexagonal architecture boundaries are preserved.
argument-hint: [task: scaffold-adapter | implement-feature | audit]
claude-skill-version: 1.0
---

# Database Explorer Architect

## Goal
Provide a concise, actionable architecture and scaffold guide for the Database Explorer project. This document defines workflows, rules, and tools for safely adding new database adapters (Oracle, ClickHouse, Databricks, etc.), implementing features, and preserving hexagonal architecture boundaries.

## Intended audience
- Platform engineers adding or maintaining adapters
- Backend developers implementing application logic
- SREs and security engineers validating deployment and access patterns

## Workflows

### 1. Scaffold a New Adapter
- Trigger: `scaffold-adapter [db-name]`
- Outcome: A new adapter skeleton under `src/adapters/driven/[db-name]/` with tests and configuration.
Steps:
1. Create the adapter package: `src/adapters/driven/[db-name]/`.
2. Implement `adapter.py` that implements the `DatabasePort` interface (see `src/core/ports`).
     - Rule: Prefer `execute_query_stream(sql, params)` which yields rows for streaming and memory efficiency; avoid loading entire result sets in memory.
3. Add `config.py` with a `pydantic` settings model for connection parameters and register secrets references (Vault/Secrets Manager).
4. Add integration tests under `tests/adapters/[db-name]/` that run against a test instance or emulator.

### 2. Implement a Feature
- Trigger: `implement-feature [short-description]`
Steps:
1. Update domain models in `src/core/domain` (entities, value objects) or add new ports in `src/core/ports` if needed.
2. Implement application services in `src/application` that orchestrate domain logic and call ports.
3. Update driving adapters (`src/adapters/driving`, e.g., FastAPI endpoints or CLI) to expose the new capability.
4. Add/adjust integration tests and documentation in `references/`.

### 3. Audit and Architecture Validation
- Trigger: `audit`
Checks:
1. Ensure domain layer has no dependencies on adapters or frameworks (no imports of `src/adapters`).
2. Ensure driving adapters (FastAPI) only call application services and do not embed domain logic.
3. Validate that all DB access goes through `DatabasePort` implementations.

## Architecture Rules (Key Principles)
- Layering: Domain (inner) -> Application -> Adapters (outer). Inner layers must not import outer layers.
- Universal types: Normalize provider-specific types to `UniversalDataType` (e.g. TEXT, INTEGER, FLOAT, TIMESTAMP) at the adapter boundary.
- Streaming-first: Use streaming (generator-based) query execution and Server-Sent Events (SSE) or chunked responses for large result sets.
- Read-only-by-default: Adapters should be implemented for read-only access unless an explicit admin capability is authorized and audited.

## Tools & Scripts
- `scripts/scaffold_adapter.py`: CLI helper to generate adapter skeletons.
- `scripts/run_query.py`: Small runner used by integration tests and local dev to exercise `DatabasePort` connectors.

## Example Invocation
CLI:
```
scaffold-adapter oracle
implement-feature "add table sampling endpoint"
audit
```

JSON example for query feature:
```
{
    "db": "oracle",
    "query": "SELECT * FROM users WHERE created_at > :since",
    "params": {"since": "2025-01-01T00:00:00Z"},
    "max_rows": 500
}
```

## I/O Schema (suggested)
- Request:
    - `db`: string (oracle|clickhouse|databricks)
    - `query`: string
    - `params`: object (optional)
    - `max_rows`: integer (optional)
- Response:
    - `status`: "ok" | "error"
    - `rows`: array of objects (can be streamed)
    - `summary`: string

## Verification
- Unit tests for domain and application layers.
- Integration tests for each adapter using test fixtures or ephemeral containers.
- Contract tests to validate `DatabasePort` behavior across adapters.

## References
- See `references/architecture.md` for architecture rules and connector requirements.

