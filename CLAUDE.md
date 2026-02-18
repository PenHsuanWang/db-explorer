# Project Context: Local Database Exploration & Cleaning Web App (Read-Only)

A local, single-machine web application for exploring remote databases in a **read-only**, **side-effect-free** manner. Raw data fetched from remote databases is normalized and cleaned entirely within the application layer (backend/frontend) — never at the database layer.

## Core Principles

1. **Web Application (not CLI):** Provides a graphical interface via a React frontend and a FastAPI backend.
2. **Read-Only (Zero Side Effects):** All database connections operate in read-only mode. No `INSERT`, `UPDATE`, `DELETE`, or `DDL` statements are ever executed against remote databases.
3. **Local Cleaning (Local-First Processing):** After raw data is fetched, all normalization, deduplication, and type casting happen inside the application layer (CleaningEngine), not in the database.

## Tech Stack

- **Language:** Python 3.12+
- **Backend:** FastAPI
- **Frontend:** React 18, Vite, TypeScript
- **Data Processing:** Pandas / Pydantic (local data cleaning and normalization)
- **Configuration:** Pydantic / Pydantic Settings
- **Database (connectors):** SQLAlchemy (Core), oracledb / cx_Oracle, clickhouse-driver
- **Testing:** Pytest, Ruff (Linter), Vitest (frontend)

## Architecture Style

- **Pattern:** Hexagonal / Layered Architecture (Ports & Adapters)
- **Key Constraints:**
  - Domain layer (`backend/src/core/domain`) has ZERO external dependencies.
  - Infrastructure (adapters) depends on Domain, never the reverse.
  - **Strict Read-Only Access:** `DatabasePort` implementations must enforce read-only connections and reject any write or DDL operations.
  - **Local-First Processing:** Data transformations (normalization, type casting, deduplication) are performed inside `CleaningEngine` after fetching, never delegated to the database.

## Data Flow

```
API (FastAPI) → DataService → CleaningEngine → DatabasePort → Remote DB
                                   ↑
                        (normalize / deduplicate /
                         type-cast in memory)
```

- **DatabasePort** — fetches raw data from remote databases (read-only).
- **CleaningEngine** — transforms raw rows into a unified `UniversalFormat` in memory.
- **API** — returns cleaned, consistently-formatted JSON to the frontend.

## Commands

```bash
# Start full stack (recommended)
docker-compose up -d

# Backend only
cd backend && poetry run uvicorn src.main:app --reload

# Frontend only
cd web-ui && npm run dev

# Run backend tests
cd backend && pytest tests/

# Lint backend
cd backend && ruff check src/ tests/

# Lint frontend
cd web-ui && npm run lint
```
