# DB Explorer — Comprehensive Architecture Review & Refactoring Plan

> **Document Type:** Software Design Document (SDD) — 2026 Formal Submission  
> **Version:** 1.0  
> **Date:** 2026-03-27  
> **Status:** Proposed  
> **Authors:** Architecture Review Board  
> **Repository:** `PenHsuanWang/db-explorer`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Reference Architecture: TaskFlow SDD](#2-reference-architecture-taskflow-sdd)
3. [Current DB Explorer Architecture Assessment](#3-current-db-explorer-architecture-assessment)
   - 3.1 [Architecture Overview](#31-architecture-overview)
   - 3.2 [Strengths](#32-strengths)
   - 3.3 [Gap Analysis](#33-gap-analysis)
4. [Design Principle Mapping: TaskFlow → DB Explorer](#4-design-principle-mapping-taskflow--db-explorer)
   - 4.1 [Directly Applicable Principles](#41-directly-applicable-principles)
   - 4.2 [Principles Requiring Adaptation](#42-principles-requiring-adaptation)
   - 4.3 [Principles That Do Not Apply](#43-principles-that-do-not-apply)
5. [Target Architecture](#5-target-architecture)
   - 5.1 [System Topology](#51-system-topology)
   - 5.2 [Request Lifecycle (Happy Path)](#52-request-lifecycle-happy-path)
6. [Data Model Design (PostgreSQL)](#6-data-model-design-postgresql)
   - 6.1 [Entity-Relationship Diagram](#61-entity-relationship-diagram)
   - 6.2 [Table Definitions](#62-table-definitions)
   - 6.3 [Design Decisions](#63-design-decisions)
7. [Phased Refactoring Plan](#7-phased-refactoring-plan)
   - Phase 0: Foundation & Infrastructure
   - Phase 1: Authentication & Authorization
   - Phase 2: Persistent State & Multi-Tenancy
   - Phase 3: Celery Task Queue & Background Jobs
   - Phase 4: SSE Real-Time Streaming
   - Phase 5: Redis Caching & Performance
   - Phase 6: Production Hardening
8. [Target File Structure](#8-target-file-structure)
9. [Architectural Constraints & Invariants](#9-architectural-constraints--invariants)
10. [Security Considerations](#10-security-considerations)
11. [Risk Assessment & Mitigation](#11-risk-assessment--mitigation)
12. [2026 SDD Compliance Checklist](#12-2026-sdd-compliance-checklist)
13. [Recommended Execution Strategy](#13-recommended-execution-strategy)
14. [Appendix A — Current vs. Target Technology Matrix](#appendix-a--current-vs-target-technology-matrix)
15. [Appendix B — Glossary](#appendix-b--glossary)

---

## 1. Executive Summary

**DB Explorer** is a local, read-only web application for exploring remote databases. It is built on a clean Hexagonal (Ports & Adapters) architecture with a FastAPI backend and a React 18 frontend. Its core strengths are pluggable database connectors, strict read-only enforcement, and in-memory data cleaning via a universal data format.

This document evaluates the **TaskFlow** reference architecture — a production-grade, multi-tenant task processing platform featuring JWT authentication, Celery-based asynchronous job orchestration, Redis state management (broker + Pub/Sub), PostgreSQL persistence, and Server-Sent Events (SSE) real-time streaming — and maps its design principles to DB Explorer's requirements.

The resulting refactoring plan transforms DB Explorer from a lightweight, single-user data exploration tool into a **production-grade, multi-tenant platform** while preserving its core architectural strengths:

- **Hexagonal Architecture** — clean domain layer, pluggable adapters
- **Read-Only Enforcement** — SQL validation at the port level
- **Local-First Processing** — all data cleaning in the application layer
- **Universal Data Format** — consistent cross-database type abstraction

The plan is organized into **seven phases** spanning approximately 8 weeks, each producing an independently deployable and testable increment.

---

## 2. Reference Architecture: TaskFlow SDD

The TaskFlow SDD describes a multi-tenant, single-machine web application framework with the following capabilities:

| Capability | Implementation |
|---|---|
| User registration & authentication | Argon2 password hashing + JWT in HTTP-Only cookies |
| Multi-tenant data isolation | `WHERE user_id = :current_user.id` on every SQL query |
| Background task processing | Celery workers with Redis as message broker |
| Real-time progress streaming | Server-Sent Events (SSE) backed by Redis Pub/Sub |
| Persistent task state | PostgreSQL with status tracking and progress metadata |
| State recovery on reconnect | `GET /me` hydrates user, `GET /tasks` hydrates task list, SSE auto-reconnects |
| Crash resilience | `acks_late=True` ensures jobs survive worker restarts |
| Dual-write progress pattern | Every progress tick writes to PostgreSQL (persistence) + Redis Pub/Sub (real-time) |

### TaskFlow Data Flow

```
Browser (AuthCtx, TaskCtx, EventSource)
    ↓ HTTP + Cookie / SSE
Nginx (:80) — static files + API proxy
    ↓
FastAPI (:8000) — auth_router, task_router, SSE endpoint
    ↓                    ↓                    ↓
PostgreSQL          Redis (Broker)       Redis (Pub/Sub)
(Users, Tasks)      (Celery Queue)       (SSE Relay)
                         ↓                    ↑
                    Celery Worker ─────────────┘
                    (process_heavy_workload)
```

### TaskFlow Core Principles

1. **Stateless API** — JWT in HTTP-Only cookies; no server-side sessions
2. **Multi-tenant isolation** — every query scoped by `user_id`
3. **Resilient background jobs** — `acks_late=True`; jobs survive worker crashes
4. **Dual-write progress** — every tick → PostgreSQL (persistence) + Redis Pub/Sub (real-time)
5. **Seamless state recovery** — page load hydrates from REST endpoints; SSE auto-reconnects for in-progress tasks

---

## 3. Current DB Explorer Architecture Assessment

### 3.1 Architecture Overview

DB Explorer follows the **Hexagonal Architecture** (Ports & Adapters) pattern with three clearly defined layers:

```
┌─────────────────────────────────────────────────────────────────┐
│  HTTP LAYER (Driving Adapters)                                  │
│  ├─ POST /api/v1/connections          (CRUD)                   │
│  ├─ POST /api/v1/search               (metadata fuzzy search)  │
│  ├─ POST /api/v1/peek                  (sample data preview)   │
│  └─ POST /api/v1/workbench             (multi-table analysis)  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                              │
│  ├─ DataService          (orchestration)                        │
│  ├─ MetadataIndexer      (SQLite search index)                  │
│  └─ CleaningEngine       (data transformation pipeline)         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  DOMAIN LAYER (Zero external dependencies)                      │
│  ├─ ConnectionConfig, SearchRequest, CleaningConfig   (models)  │
│  ├─ UniversalDataType, UniversalCell, UniversalRow    (types)   │
│  └─ DatabasePort                                  (interface)   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  DRIVEN ADAPTERS (Database Implementations)                     │
│  ├─ MockConnector        (in-memory, demo/testing)              │
│  ├─ OracleConnector      (oracledb)                             │
│  ├─ ClickHouseConnector  (clickhouse-driver)                    │
│  └─ DatabricksConnector  (databricks-sql-connector)             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    REMOTE DATABASES (read-only)
```

### 3.2 Strengths

| Capability | Current Implementation | Assessment |
|---|---|---|
| **Hexagonal Architecture** | Clean Ports & Adapters with Domain, Application, and Adapter layers | ✅ Excellent — ready for extension |
| **Domain Layer Isolation** | `core/domain/` has zero external dependencies | ✅ Excellent — aligns with TaskFlow principles |
| **Read-Only Enforcement** | `DatabasePort._validate_read_only()` with keyword blocklist + regex validation | ✅ Excellent — security invariant preserved |
| **Universal Data Format** | `UniversalDataType` enum, `UniversalCell`, `UniversalRow` | ✅ Excellent — consistent cross-DB abstraction |
| **CleaningEngine Pipeline** | Null unification → deduplication (SHA256) → type casting → formatting | ✅ Excellent — local-first processing |
| **Pluggable Connectors** | `ConnectorFactory` registry pattern with 4 implementations | ✅ Excellent — extensible adapter pattern |
| **Pydantic Configuration** | `pydantic-settings` with environment-driven config | ✅ Good — easily extensible |
| **Frontend Modularity** | Hooks + Services + CSS Modules + TypeScript types | ✅ Good — clean separation of concerns |
| **Test Coverage** | 15+ unit/integration tests covering domain, cleaning, service, connector layers | ✅ Good — solid foundation |

### 3.3 Gap Analysis

| Capability (from TaskFlow) | DB Explorer Status | Priority | Complexity |
|---|---|---|---|
| **User Authentication (JWT + Argon2)** | ❌ Not implemented — all endpoints are public | 🔴 Critical | Medium |
| **Multi-Tenant Data Isolation** | ❌ Not implemented — global shared state | 🔴 Critical | High |
| **Redis State Store (cache + Pub/Sub)** | ❌ Not used — in-memory singletons only | 🟡 High | Medium |
| **Celery Task Queue** | ❌ Not implemented — all operations synchronous | 🟡 High | High |
| **SSE Real-Time Streaming** | ❌ Not implemented — request/response only | 🟡 High | Medium |
| **PostgreSQL Persistence** | ❌ SQLite in-memory only (volatile) | 🟡 High | Medium |
| **Alembic Schema Migrations** | ❌ No schema versioning | 🟡 High | Low |
| **Nginx Reverse Proxy** | ❌ Direct port access | 🟢 Medium | Low |
| **Frontend Auth Context** | ❌ No authentication state management | 🔴 Critical | Medium |
| **Frontend URL Routing (react-router)** | ❌ View-state switching only, no URL routing | 🟢 Medium | Low |
| **Frontend Job/Task Context (SSE)** | ❌ No real-time updates | 🟡 High | Medium |
| **Frontend Theme Context** | ❌ Hardcoded dark theme, no user preference | 🟢 Low | Low |
| **Production Docker Build** | ❌ Dev-only docker-compose (no multi-stage builds) | 🟡 High | Medium |
| **Gunicorn Process Manager** | ❌ Single uvicorn process | 🟢 Medium | Low |
| **Frontend Error Boundaries** | ❌ Not implemented | 🟢 Medium | Low |
| **Structured Logging** | ❌ Basic Python logging only | 🟢 Medium | Low |

---

## 4. Design Principle Mapping: TaskFlow → DB Explorer

### 4.1 Directly Applicable Principles

| TaskFlow Principle | DB Explorer Application |
|---|---|
| **Stateless API (JWT in HTTP-Only cookies)** | Add JWT-based authentication to FastAPI. Use HTTP-Only cookies (not Authorization headers) to prevent XSS token theft. No server-side sessions. |
| **Multi-tenant isolation (WHERE user_id)** | Every user's connections, saved workbenches, and job history scoped by `user_id`. Middleware-level injection ensures no query forgets the filter. |
| **Dual-write progress (DB + Pub/Sub)** | Apply to long-running operations: Deep Search (scanning data values), metadata reindexing, and large multi-table workbench loads. Write progress to PostgreSQL (persistence) and Redis Pub/Sub (real-time). |
| **Seamless state recovery** | On page load: `GET /auth/me` hydrates user profile → `GET /connections` hydrates user's connections → SSE reconnects for in-progress background jobs. |
| **Resilient background jobs (acks_late)** | Deep search and metadata reindex jobs survive Celery worker crashes. PostgreSQL is the ground truth for job state. |

### 4.2 Principles Requiring Adaptation

| TaskFlow Principle | DB Explorer Adaptation | Rationale |
|---|---|---|
| **Generic `process_heavy_workload`** | Domain-specific tasks: `deep_search_job`, `reindex_metadata_job`, `export_workbench_job` | DB Explorer has specialized long-running operations, not generic task processing |
| **Task CRUD** | → **Job CRUD** for deep searches, metadata crawls, and workbench exports | Users don't "create tasks" — they trigger searches that may become background jobs |
| **PostgreSQL for Users + Tasks** | → PostgreSQL for Users + Connections + Jobs + Saved Workbenches | Additional tables needed for DB Explorer's domain |
| **SSE per task** | → **SSE per job** (deep search progress, metadata reindex progress) | SSE endpoints scoped to specific background job types |
| **User creates arbitrary tasks** | System dispatches jobs automatically (deep search toggle, scheduled reindex) | Users trigger domain operations; the system decides whether to run synchronously or asynchronously |

### 4.3 Principles That Do Not Apply

| TaskFlow Principle | Reason for Exclusion |
|---|---|
| **Write operations to remote databases** | DB Explorer is strictly read-only — the `DatabasePort._validate_read_only()` guard is a core architectural invariant. No INSERT, UPDATE, DELETE, or DDL operations are ever executed against remote databases. |
| **Task result persistence in DB rows** | Deep search results are transient metadata matches returned inline. They are not persistent artifacts requiring long-term storage. |

---

## 5. Target Architecture

### 5.1 System Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                          BROWSER                                │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ AuthCtx  │  │ConnectionCtx │  │  EventSource (SSE)       │  │
│  │ /auth/me │  │ /connections │  │  /jobs/{id}/stream       │  │
│  └────┬─────┘  └──────┬───────┘  └────────────┬─────────────┘  │
│       │               │                       │                │
└───────┼───────────────┼───────────────────────┼────────────────┘
        │  HTTP+Cookie  │   HTTP+Cookie         │ SSE stream
        │               │                       │
┌───────▼───────────────▼───────────────────────▼────────────────┐
│                      NGINX  (:80)                              │
│  Static files:  /        →  React SPA (built assets)           │
│  API proxy:     /api/*   →  FastAPI (:8000)                    │
│  SSE config:    proxy_buffering off; X-Accel-Buffering: no     │
└───────┬───────────────┬───────────────────────┬────────────────┘
        │               │                       │
┌───────▼───────────────▼───────────────────────▼────────────────┐
│             FastAPI  (:8000)  [Gunicorn + Uvicorn Workers]     │
│                                                                │
│  ┌────────────┐ ┌──────────────┐ ┌─────────────────────────┐  │
│  │auth_router │ │ data_router  │ │ job_router (CRUD + SSE) │  │
│  │JWT cookie  │ │ connections  │ │ Redis Pub/Sub listener  │  │
│  │register    │ │ search       │ │ /jobs (list)            │  │
│  │login       │ │ peek         │ │ /jobs/{id} (status)     │  │
│  │logout      │ │ workbench    │ │ /jobs/{id}/stream (SSE) │  │
│  │me          │ │              │ │                         │  │
│  └─────┬──────┘ └──────┬──────┘ └──────────┬──────────────┘  │
│        │               │                   │                   │
│        ▼               ▼                   ▼                   │
│  ┌──────────┐   ┌────────────┐       ┌───────────┐            │
│  │PostgreSQL│   │   Redis    │       │   Redis   │            │
│  │ users    │   │  (Celery   │       │  (Pub/Sub │            │
│  │ conns    │   │   Broker + │       │   + Cache)│            │
│  │ jobs     │   │   Result   │       │           │            │
│  │ saved_wb │   │   Backend) │       │           │            │
│  └──────────┘   └─────┬──────┘       └───────────┘            │
│                       │                     ▲                  │
└───────────────────────┼─────────────────────┼──────────────────┘
                        │                     │
┌───────────────────────▼─────────────────────┼──────────────────┐
│                 CELERY WORKER               │                  │
│                                             │                  │
│  deep_search_job(user_id, search_request)   │                  │
│    1. Load user's connections from DB       │                  │
│    2. For each connection:                  │                  │
│       a) execute_safe_read(scan query)      │                  │
│       b) UPDATE jobs SET progress_meta=...  │ ◄── DB write     │
│       c) redis.publish(job:{id}, progress)  │ ◄── Pub/Sub      │
│    3. UPDATE jobs SET status=SUCCESS        │                  │
│    4. redis.publish(job:{id}, complete) ────┘                  │
│                                                                │
│  reindex_metadata_job(user_id, connection_id)                  │
│    1. Crawl tables and columns via DatabasePort                │
│    2. Rebuild MetadataIndexer for user                         │
│    3. Report progress via dual-write                           │
│                                                                │
│  export_workbench_job(user_id, workbench_request)              │
│    1. Fetch multi-table data                                   │
│    2. Apply cleaning pipeline                                  │
│    3. Write result to jobs.result_data                         │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Request Lifecycle (Happy Path)

#### Synchronous Path (Normal Search / Peek)

1. **User submits search query** → `POST /api/v1/search` with JWT cookie
2. **FastAPI** validates JWT, extracts `user_id`, calls `DataService.search(request, user_id)`
3. **DataService** queries `MetadataIndexer` (scoped by user's connections), returns results
4. **React** renders search results immediately

#### Asynchronous Path (Deep Search)

1. **User enables "Deep Search" toggle** → `POST /api/v1/jobs` with JWT cookie
2. **FastAPI** validates JWT, creates a `jobs` row with `PENDING`, calls `celery.delay()`, returns `202 Accepted` with `job_id`
3. **React** receives `job_id`, opens `EventSource` to `/api/v1/jobs/{id}/stream`
4. **Celery Worker** picks up the job from Redis, writes `STARTED` to DB + Pub/Sub
5. **SSE endpoint** subscribes to `job_progress:{id}` channel, relays events to browser
6. **Worker** iterates through connections, writes `PROGRESS` + `progress_meta` to DB + Pub/Sub on each step
7. **Browser** receives SSE events, updates progress bar in real time
8. **Worker** finishes, writes `SUCCESS` + `result_data` to DB + Pub/Sub
9. **SSE stream** detects terminal status, sends final event, closes
10. **On page refresh**, React calls `GET /auth/me` → `GET /jobs`, sees `SUCCESS`, renders results — no SSE needed

---

## 6. Data Model Design (PostgreSQL)

### 6.1 Entity-Relationship Diagram

```
┌─────────────────────────┐     ┌───────────────────────────────┐
│         users           │     │         connections            │
├─────────────────────────┤     ├───────────────────────────────┤
│ id          UUID   [PK] │◄──┐ │ id            UUID    [PK]   │
│ email       VARCHAR [UQ]│   │ │ user_id       UUID    [FK]───┤
│ username    VARCHAR [UQ]│   │ │ name          VARCHAR        │
│ hashed_pw   VARCHAR     │   │ │ db_type       VARCHAR        │
│ is_active   BOOLEAN     │   │ │ host          VARCHAR        │
│ created_at  TIMESTAMPTZ │   │ │ port          INTEGER        │
│ updated_at  TIMESTAMPTZ │   │ │ database_name VARCHAR        │
└─────────────────────────┘   │ │ encrypted_creds BYTEA        │
                              │ │ extra_params  JSONB           │
                              │ │ created_at    TIMESTAMPTZ     │
                              │ │ updated_at    TIMESTAMPTZ     │
                              │ └───────────────────────────────┘
                              │
                              │ ┌───────────────────────────────┐
                              │ │           jobs                │
                              │ ├───────────────────────────────┤
                              ├─┤ user_id       UUID    [FK]   │
                              │ │ id            UUID    [PK]   │
                              │ │ job_type      VARCHAR        │
                              │ │ status        VARCHAR        │
                              │ │ payload       JSONB          │
                              │ │ progress_meta JSONB          │
                              │ │ result_data   JSONB          │
                              │ │ error_message TEXT           │
                              │ │ created_at    TIMESTAMPTZ    │
                              │ │ updated_at    TIMESTAMPTZ    │
                              │ └───────────────────────────────┘
                              │
                              │ ┌───────────────────────────────┐
                              │ │     saved_workbenches         │
                              │ ├───────────────────────────────┤
                              └─┤ user_id       UUID    [FK]   │
                                │ id            UUID    [PK]   │
                                │ name          VARCHAR        │
                                │ panes_config  JSONB          │
                                │ cleaning_cfg  JSONB          │
                                │ created_at    TIMESTAMPTZ    │
                                │ updated_at    TIMESTAMPTZ    │
                                └───────────────────────────────┘
```

### 6.2 Table Definitions

#### `users`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Unique user identifier |
| `email` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL` | User email address |
| `username` | `VARCHAR(100)` | `UNIQUE`, `NOT NULL` | Display name |
| `hashed_pw` | `VARCHAR(255)` | `NOT NULL` | Argon2id password hash |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | Soft-delete flag |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Account creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Last update timestamp |

#### `connections`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Unique connection identifier |
| `user_id` | `UUID` | `FOREIGN KEY → users(id)`, `NOT NULL` | Owner user |
| `name` | `VARCHAR(255)` | `NOT NULL` | Human-readable connection name |
| `db_type` | `VARCHAR(50)` | `NOT NULL` | Database type (`oracle`, `clickhouse`, `databricks`, `mock`) |
| `host` | `VARCHAR(255)` | | Connection hostname |
| `port` | `INTEGER` | | Connection port |
| `database_name` | `VARCHAR(255)` | | Database/catalog name |
| `encrypted_creds` | `BYTEA` | | Fernet-encrypted credentials blob |
| `extra_params` | `JSONB` | `DEFAULT '{}'` | Additional parameters (e.g., `http_path` for Databricks) |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Last update timestamp |

#### `jobs`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Unique job identifier |
| `user_id` | `UUID` | `FOREIGN KEY → users(id)`, `NOT NULL` | Owner user |
| `job_type` | `VARCHAR(50)` | `NOT NULL` | Job type (`deep_search`, `metadata_reindex`, `workbench_export`) |
| `status` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'PENDING'` | Job status (`PENDING`, `STARTED`, `PROGRESS`, `SUCCESS`, `FAILURE`) |
| `payload` | `JSONB` | | Input parameters (search query, connection IDs, etc.) |
| `progress_meta` | `JSONB` | | Progress state: `{"current": 3, "total": 10, "percent": 30, "message": "..."}` |
| `result_data` | `JSONB` | | Output data (search results, export data) |
| `error_message` | `TEXT` | | Error details on failure |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Job creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Last status update timestamp |

#### `saved_workbenches`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Unique workbench identifier |
| `user_id` | `UUID` | `FOREIGN KEY → users(id)`, `NOT NULL` | Owner user |
| `name` | `VARCHAR(255)` | `NOT NULL` | Workbench name |
| `panes_config` | `JSONB` | `NOT NULL` | Pane layout and table references |
| `cleaning_cfg` | `JSONB` | `DEFAULT '{}'` | Cleaning configuration snapshot |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Last update timestamp |

### 6.3 Design Decisions

- **`encrypted_creds` (BYTEA):** Connection credentials are encrypted at rest using Fernet symmetric encryption. The encryption key is stored as an environment variable (`ENCRYPTION_KEY`), never in the database or source code.
- **`progress_meta` (JSONB):** Flexible structure enables different job types to report domain-specific progress without schema changes.
- **`job_type` (VARCHAR):** Enum-like constraint enforced at the application layer (Pydantic validation), allowing new job types without migrations.
- **`status` (VARCHAR):** Matches TaskFlow's status values: `PENDING → STARTED → PROGRESS → SUCCESS | FAILURE`.
- **All queries include `WHERE user_id = :current_user_id`** — multi-tenant isolation enforced at the SQL level.
- **Soft-delete via `is_active`:** Users are deactivated, not deleted, to preserve referential integrity.

---

## 7. Phased Refactoring Plan

### Phase 0 — Foundation & Infrastructure (Week 1–2)

**Goal:** Add infrastructure services (PostgreSQL, Redis, Nginx) and backend dependencies without changing existing functionality.

| ID | Task | Details |
|---|---|---|
| P0.1 | Add PostgreSQL and Redis to `docker-compose.yml` | PostgreSQL 16 (Alpine), Redis 7 (Alpine), persistent volumes, health checks |
| P0.2 | Add backend dependencies | `sqlalchemy[asyncio]`, `asyncpg`, `psycopg2-binary`, `alembic`, `redis`, `celery[redis]`, `pwdlib[argon2]`, `python-jose[cryptography]`, `sse-starlette` |
| P0.3 | Create async SQLAlchemy engine | New `backend/src/infrastructure/database.py` with async engine, session factory, and `get_db_session` dependency |
| P0.4 | Create ORM models | New `backend/src/core/domain/orm_models.py` for `users`, `connections`, `jobs`, `saved_workbenches` |
| P0.5 | Initialize Alembic | First migration creates all four tables |
| P0.6 | Extend `Settings` class | Add `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`, `ENCRYPTION_KEY` |
| P0.7 | Add Nginx reverse proxy | New `nginx/nginx.conf` with static file serving, API proxy, SSE configuration |
| P0.8 | Create production Dockerfiles | Multi-stage backend (gunicorn + uvicorn workers), multi-stage frontend (build → nginx) |

**Exit Criteria:** `docker-compose up` starts all services (FastAPI, PostgreSQL, Redis, Nginx). Existing endpoints still work. Alembic migration runs successfully.

---

### Phase 1 — Authentication & Authorization (Week 2–3)

**Goal:** Add user registration, login, and JWT-based authentication. Protect all existing endpoints.

| ID | Task | Details |
|---|---|---|
| P1.1 | Create Pydantic auth schemas | `UserCreate`, `UserLogin`, `UserResponse`, `TokenPayload` in `core/domain/models.py` |
| P1.2 | Implement auth service | `application/auth_service.py`: `register()`, `login()`, `get_current_user()` with Argon2id hashing |
| P1.3 | Implement JWT utilities | `infrastructure/security.py`: `create_access_token()`, `decode_token()`, cookie configuration |
| P1.4 | Create `auth_router` | `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` |
| P1.5 | Create `get_current_user` dependency | Extract JWT from HTTP-Only cookie, validate, return `User` object |
| P1.6 | Protect all existing routers | Add `Depends(get_current_user)` to connections, search, peek, workbench endpoints |
| P1.7 | Frontend: `AuthContext` provider | React context with `login()`, `register()`, `logout()`, `user` state, session hydration via `GET /auth/me` |
| P1.8 | Frontend: Login/Register pages | Form components with validation and error handling |
| P1.9 | Frontend: Install `react-router-dom` | URL-based routing: `/login`, `/register`, `/`, `/workbench`, `/jobs` |
| P1.10 | Frontend: Axios 401 interceptor | Auto-redirect to `/login` on 401 responses |

**Exit Criteria:** Users can register, login, and access protected endpoints. Unauthenticated requests receive 401. Frontend shows login page for unauthenticated users.

---

### Phase 2 — Persistent State & Multi-Tenancy (Week 3–4)

**Goal:** Migrate from in-memory state to PostgreSQL persistence. Enforce per-user data isolation.

| ID | Task | Details |
|---|---|---|
| P2.1 | Persist connections to PostgreSQL | Migrate `ConnectorFactory` in-memory dict → `connections` table. Load on demand, cache in factory. |
| P2.2 | Implement credential encryption | `infrastructure/security.py`: Fernet encrypt/decrypt for connection passwords. Encryption key from env. |
| P2.3 | Add `user_id` scoping | All connection/search/peek/workbench operations filter by `user_id`. Service layer receives `user_id` from dependency injection. |
| P2.4 | Migrate MetadataIndexer | Add `user_id` column to SQLite index. Alternatively, move to PostgreSQL with `LIKE` queries on a `metadata` table scoped by user. |
| P2.5 | Implement saved workbenches | CRUD for `saved_workbenches` table: `POST /workbenches`, `GET /workbenches`, `GET /workbenches/{id}`, `DELETE /workbenches/{id}` |
| P2.6 | Frontend: `ConnectionContext` | Persistent connection state from backend, with add/remove operations |
| P2.7 | Frontend: Saved workbench UI | Save/load/delete workbench configurations |
| P2.8 | Multi-tenant integration tests | Verify User A cannot see User B's connections, search results, or workbenches |

**Exit Criteria:** State survives server restart. Each user sees only their own data. Automated tests confirm isolation.

---

### Phase 3 — Celery Task Queue & Background Jobs (Week 4–5)

**Goal:** Offload long-running operations to Celery workers. Add job tracking.

| ID | Task | Details |
|---|---|---|
| P3.1 | Create Celery app | `infrastructure/celery_app.py` with Redis broker, PostgreSQL result backend |
| P3.2 | Implement `deep_search_job` | Celery task: iterate user's connections, scan data values, write progress via dual-write (DB + Pub/Sub) |
| P3.3 | Implement `reindex_metadata_job` | Celery task: re-crawl all user's connections, rebuild metadata index, report progress |
| P3.4 | Create `job_router` | `POST /jobs` (dispatch), `GET /jobs` (list user's jobs), `GET /jobs/{id}` (status), `DELETE /jobs/{id}` (cancel) |
| P3.5 | Configure crash resilience | `acks_late=True`, `reject_on_worker_lost=True` for all tasks |
| P3.6 | Add Celery worker to Docker | New service in `docker-compose.yml` sharing backend code, connecting to Redis + PostgreSQL |
| P3.7 | Frontend: Job dispatch UI | Deep search triggers background job with "Running in background..." indicator |
| P3.8 | Frontend: Job list/status page | Dashboard showing running/completed/failed jobs with status |

**Exit Criteria:** Deep search runs asynchronously. Job status is trackable. Jobs survive worker restarts.

---

### Phase 4 — SSE Real-Time Streaming (Week 5–6)

**Goal:** Stream real-time progress from Celery workers to the browser via Server-Sent Events.

| ID | Task | Details |
|---|---|---|
| P4.1 | Implement SSE endpoint | `GET /jobs/{id}/stream` using `sse-starlette`. Subscribe to Redis `job_progress:{id}` channel. Verify job ownership (multi-tenant). Auto-close on terminal status. |
| P4.2 | Configure Nginx for SSE | `proxy_buffering off`, `X-Accel-Buffering: no`, appropriate timeouts (keep-alive), `Connection: ''` |
| P4.3 | Frontend: `useJobStream` hook | React hook using `EventSource`. Auto-reconnect on connection loss. Parse SSE events, update job progress state. |
| P4.4 | Frontend: Progress bar component | Real-time progress bar with percentage, step count, and status message |
| P4.5 | State recovery on reconnect | On page load: hydrate from `GET /jobs`, open SSE only for jobs with `status` in (`PENDING`, `STARTED`, `PROGRESS`) |

**Exit Criteria:** User sees real-time progress bar during deep search. Progress survives page refresh (reconnects via SSE). Terminal events close the stream.

---

### Phase 5 — Redis Caching & Performance (Week 6–7)

**Goal:** Add caching layer for frequently accessed data to reduce database load.

| ID | Task | Details |
|---|---|---|
| P5.1 | Add Redis caching layer | Cache metadata search results (TTL: 5 min), connection lists (TTL: 1 min), peek results (TTL: 2 min, keyed by `connection+table+cleaning_config` hash) |
| P5.2 | Implement cache invalidation | Clear relevant cache keys on: connection add/remove, metadata reindex, cleaning config change |
| P5.3 | Add Redis health check | Include Redis status in `/health` endpoint response |
| P5.4 | Frontend: Client-side caching | Stale-while-revalidate pattern for search results. Debounced search input. |

**Exit Criteria:** Repeated searches are served from cache. Cache invalidation works correctly. App functions without Redis (graceful degradation).

---

### Phase 6 — Production Hardening (Week 7–8)

**Goal:** Harden the system for production deployment with security, observability, and resilience.

| ID | Task | Details |
|---|---|---|
| P6.1 | Rate limiting | Per-user, per-endpoint rate limits (e.g., 10 connections/min, 60 searches/min) |
| P6.2 | Correlation IDs | Middleware that assigns a UUID to each request, propagated through logs and responses |
| P6.3 | Structured logging | JSON-formatted logs with timestamp, level, correlation ID, user ID, endpoint |
| P6.4 | Service health checks | `/health` endpoint returning status of FastAPI, PostgreSQL, Redis, Celery |
| P6.5 | CSRF protection | Double-submit cookie pattern or `SameSite=Strict` + custom header check |
| P6.6 | Graceful shutdown | Drain Celery tasks on SIGTERM, close DB connection pools, finalize in-flight requests |
| P6.7 | Frontend: Error boundaries | React `ErrorBoundary` components at route and component level |
| P6.8 | Frontend: Loading & error states | Skeleton loaders, retry buttons, toast notifications for all async operations |
| P6.9 | End-to-end integration tests | Full flow: register → login → add connection → search → deep search → SSE progress → result |
| P6.10 | Security audit | Dependency vulnerability scanning, secret rotation mechanism, CORS policy review |

**Exit Criteria:** Production deployment checklist complete. All security controls in place. Observability stack operational.

---

## 8. Target File Structure

```
db-explorer/
├── docs/
│   └── architecture-review-and-refactoring-plan.md    # This document
├── backend/
│   ├── src/
│   │   ├── adapters/
│   │   │   ├── driven/                                # (existing — unchanged)
│   │   │   │   ├── factory.py
│   │   │   │   ├── mock.py
│   │   │   │   ├── oracle.py
│   │   │   │   ├── clickhouse.py
│   │   │   │   └── databricks.py
│   │   │   └── driving/
│   │   │       └── api/v1/
│   │   │           ├── router.py                      # (updated — include new routers)
│   │   │           ├── connections.py                  # (updated — user_id scoping)
│   │   │           ├── search.py                       # (updated — async dispatch)
│   │   │           ├── peek.py                         # (updated — user_id scoping)
│   │   │           ├── workbench.py                    # (updated — save/load + user_id)
│   │   │           ├── auth.py                         # ← NEW: auth router
│   │   │           └── jobs.py                         # ← NEW: job CRUD + SSE
│   │   ├── application/
│   │   │   ├── data_service.py                         # (updated — user-scoped)
│   │   │   ├── metadata_indexer.py                     # (updated — user-scoped)
│   │   │   ├── cleaning_engine.py                      # (unchanged)
│   │   │   ├── auth_service.py                         # ← NEW: auth business logic
│   │   │   └── job_service.py                          # ← NEW: job orchestration
│   │   ├── core/
│   │   │   ├── domain/
│   │   │   │   ├── models.py                           # (updated — User, Job schemas)
│   │   │   │   ├── types.py                            # (unchanged)
│   │   │   │   └── orm_models.py                       # ← NEW: SQLAlchemy ORM
│   │   │   └── ports/
│   │   │       ├── database.py                         # (unchanged)
│   │   │       ├── auth.py                             # ← NEW: auth port interface
│   │   │       └── job_queue.py                        # ← NEW: task queue port
│   │   ├── infrastructure/                              # ← NEW DIRECTORY
│   │   │   ├── database.py                             # Async SQLAlchemy engine
│   │   │   ├── redis.py                                # Redis client wrapper
│   │   │   ├── celery_app.py                           # Celery configuration
│   │   │   ├── security.py                             # JWT + Argon2 + Fernet
│   │   │   └── migrations/                             # Alembic
│   │   │       ├── alembic.ini
│   │   │       ├── env.py
│   │   │       └── versions/
│   │   │           └── 001_initial_schema.py
│   │   ├── config.py                                   # (updated — new settings)
│   │   ├── dependencies.py                             # (updated — new DI bindings)
│   │   └── main.py                                     # (updated — middleware, lifespan)
│   ├── tests/
│   │   ├── conftest.py                                 # (updated — new fixtures)
│   │   ├── unit/
│   │   │   ├── test_domain_models.py                   # (existing)
│   │   │   ├── test_cleaning_engine.py                 # (existing)
│   │   │   ├── test_data_service.py                    # (existing)
│   │   │   ├── test_auth_service.py                    # ← NEW
│   │   │   └── test_job_service.py                     # ← NEW
│   │   └── integration/
│   │       ├── test_mock_connector.py                  # (existing)
│   │       ├── test_auth_flow.py                       # ← NEW
│   │       ├── test_multi_tenant.py                    # ← NEW
│   │       └── test_job_lifecycle.py                   # ← NEW
│   └── pyproject.toml                                  # (updated — new deps)
├── web-ui/
│   ├── src/
│   │   ├── contexts/                                    # ← NEW DIRECTORY
│   │   │   ├── AuthContext.tsx                          # JWT session management
│   │   │   ├── ConnectionContext.tsx                    # Persistent connections
│   │   │   └── JobContext.tsx                           # Job tracking + SSE
│   │   ├── pages/                                       # ← NEW DIRECTORY
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── SearchPage.tsx                          # (refactored from App.tsx)
│   │   │   ├── ResultsPage.tsx
│   │   │   ├── WorkbenchPage.tsx
│   │   │   └── JobsPage.tsx                            # ← NEW
│   │   ├── components/                                  # (existing — updated)
│   │   │   ├── ProtectedRoute.tsx                      # ← NEW: auth guard
│   │   │   ├── JobProgressBar.tsx                      # ← NEW: SSE-driven
│   │   │   ├── ErrorBoundary.tsx                       # ← NEW
│   │   │   └── (existing components unchanged)
│   │   ├── hooks/
│   │   │   ├── useJobStream.ts                         # ← NEW: EventSource hook
│   │   │   └── (existing hooks unchanged)
│   │   ├── services/
│   │   │   ├── authService.ts                          # ← NEW: auth API calls
│   │   │   ├── jobService.ts                           # ← NEW: job API calls
│   │   │   └── (existing services unchanged)
│   │   └── types/
│   │       ├── auth.ts                                 # ← NEW: User, Token types
│   │       ├── job.ts                                  # ← NEW: Job, Progress types
│   │       └── (existing types unchanged)
│   └── package.json                                    # (updated — react-router-dom)
├── nginx/
│   └── nginx.conf                                      # ← NEW: reverse proxy config
├── docker-compose.yml                                  # (updated — all services)
└── (existing files unchanged)
```

---

## 9. Architectural Constraints & Invariants

The following invariants **must be preserved** throughout all refactoring phases:

| Invariant | Enforcement Mechanism | Rationale |
|---|---|---|
| **Read-Only Remote DB Access** | `DatabasePort._validate_read_only()` rejects INSERT, UPDATE, DELETE, DDL keywords. Connectors set read-only mode at the connection level (e.g., `SET TRANSACTION READ ONLY`). | Core security guarantee. All new code paths (auth, jobs, Celery workers) access remote databases exclusively through `DatabasePort`. |
| **Local-First Data Processing** | `CleaningEngine` transforms data in-memory after fetching. No SQL functions for normalization, dedup, or type casting. | Ensures database-agnostic cleaning. The pipeline is predictable and testable without database connections. |
| **Domain Layer Independence** | `core/domain/` has zero imports from `fastapi`, `sqlalchemy`, `celery`, `redis`, or any infrastructure package. | Enables unit testing without infrastructure. Domain models are portable across frameworks. |
| **Hexagonal Layer Direction** | Infrastructure → Application → Domain (never the reverse). Adapters depend on ports, not on each other. | Prevents tight coupling. Any adapter (connector, router, Celery) can be replaced without affecting domain logic. |
| **Multi-Tenant Isolation** | Every SQL query to the local PostgreSQL includes `WHERE user_id = :current_user_id`. Service layer receives `user_id` from dependency injection, never from request body. | Prevents data leakage between users. The `user_id` is extracted from the validated JWT, not from client-supplied data. |

### Divergences from TaskFlow (By Design)

| TaskFlow Pattern | DB Explorer Adaptation | Rationale |
|---|---|---|
| Generic `process_heavy_workload` task | Domain-specific `deep_search_job`, `reindex_metadata_job`, `export_workbench_job` | DB Explorer has specialized operations with different progress semantics |
| Task results stored in DB row | Deep search results returned inline or as cached metadata | Search results are transient matches, not persistent artifacts |
| User creates arbitrary tasks | System dispatches jobs automatically | Users trigger domain operations; the system decides sync vs. async |
| SSE for all tasks | SSE only for long-running operations | Normal search/peek/workbench are fast enough for synchronous response |

---

## 10. Security Considerations

| Control | Implementation | Phase |
|---|---|---|
| **Authentication** | Argon2id password hashing (`pwdlib[argon2]`). JWT tokens in HTTP-Only, Secure, SameSite=Lax cookies. Token expiry: 30 minutes (configurable). | Phase 1 |
| **Authorization** | `get_current_user` FastAPI dependency extracts and validates JWT on every request. Returns 401 for invalid/expired tokens. | Phase 1 |
| **CSRF Protection** | SameSite cookie attribute + custom header check (`X-Requested-With`). Consider double-submit cookie pattern for state-changing operations. | Phase 6 |
| **Credential Encryption** | Connection passwords encrypted with Fernet (symmetric) before PostgreSQL storage. Encryption key from `ENCRYPTION_KEY` environment variable. Key rotation supported. | Phase 2 |
| **Multi-Tenant Isolation** | `user_id` extracted from JWT (not client input). All database queries scoped by `user_id`. Integration tests verify isolation. | Phase 2 |
| **Read-Only Enforcement** | Unchanged from current implementation. `DatabasePort._validate_read_only()` is the security boundary for remote database access. | Existing |
| **Rate Limiting** | Per-user, per-endpoint limits. Implemented as FastAPI middleware with Redis-backed counters. | Phase 6 |
| **Input Validation** | Pydantic models validate all request bodies. SQL identifiers validated with `_SAFE_IDENTIFIER_RE` regex. | Existing + Phase 0 |
| **Secret Management** | All secrets (`JWT_SECRET`, `ENCRYPTION_KEY`, `DATABASE_URL`) from environment variables. Never in source code or Docker images. `.env` files in `.gitignore`. | Phase 0 |
| **Dependency Scanning** | Regular vulnerability scanning of Python and npm dependencies. Automated via CI/CD pipeline. | Phase 6 |

---

## 11. Risk Assessment & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| **Breaking read-only guarantees** | 🔴 Critical | Low | All new code paths (auth, jobs) only touch local PostgreSQL. Remote DB access still goes through `DatabasePort` with SQL validation. Automated tests verify read-only enforcement. |
| **Multi-tenant data leak** | 🔴 Critical | Medium | Middleware-level `user_id` injection (not manual per-query). Automated integration tests verify isolation between two users. Code review checklist includes tenant scoping check. |
| **Celery worker crash losing jobs** | 🟡 High | Medium | `acks_late=True` + `reject_on_worker_lost=True`. PostgreSQL is ground truth for job state. Worker reconnects automatically. |
| **Redis single point of failure** | 🟡 High | Low | Redis used for cache + Pub/Sub (ephemeral data). PostgreSQL is source of truth. App degrades gracefully: no SSE, no cache, but all CRUD operations still work. |
| **Migration complexity** | 🟡 High | Medium | Phased rollout: each phase is independently deployable and testable. Feature flags for gradual migration. |
| **Frontend state complexity** | 🟡 Medium | Medium | React Context pattern (not Redux) keeps complexity manageable. Each context is self-contained with clear boundaries. |
| **JWT token theft** | 🟡 Medium | Low | HTTP-Only cookies prevent JavaScript access. Secure flag requires HTTPS. Short expiry (30 min) limits exposure. |
| **Encryption key compromise** | 🔴 Critical | Low | Key rotation mechanism: re-encrypt all credentials with new key. Old key kept for decryption during rotation window. |
| **Performance regression from PostgreSQL** | 🟡 Medium | Medium | Connection pooling (SQLAlchemy async pool). Redis caching for hot paths. Benchmark before/after each phase. |

---

## 12. 2026 SDD Compliance Checklist

| 2026 SDD Principle | Status | Implementation |
|---|---|---|
| **API-First Design** | ✅ Ready | OpenAPI 3.1 auto-generated by FastAPI. Pydantic schemas define all API contracts. Frontend consumes typed API client. |
| **Infrastructure as Code** | 🔄 Phase 0 | Complete `docker-compose.yml` with all services. Nginx config versioned. Alembic migrations versioned. |
| **Schema-Driven Development** | 🔄 Phase 0 | Alembic manages all DB schema changes. Pydantic schemas enforce API contracts. TypeScript interfaces mirror backend schemas. |
| **Observability (Logs, Metrics, Traces)** | 🔄 Phase 6 | Structured JSON logging with correlation IDs. Health check endpoints for all services. Prometheus-compatible metrics (future). |
| **Security by Default** | 🔄 Phase 1–6 | JWT + CSRF + encrypted credentials + row-level isolation + read-only enforcement + rate limiting + dependency scanning. |
| **Testability** | ✅ Ready | Hexagonal architecture enables unit testing without infrastructure. Integration tests for full flows. Domain layer testable in isolation. |
| **Graceful Degradation** | 🔄 Phase 5–6 | App works without Redis (no caching/SSE, but functional). App works without Celery (deep search runs synchronously). |
| **CI/CD Ready** | 🔄 Phase 6 | Multi-stage Docker builds. Alembic migrations run on startup. Health checks for orchestration readiness probes. |
| **Documentation as Code** | ✅ Ready | API docs auto-generated by FastAPI (`/docs`, `/redoc`). Architecture decisions documented in `docs/`. |
| **Dependency Hygiene** | 🔄 Phase 0 | All dependencies pinned with version ranges. Optional DB drivers declared separately. Regular vulnerability scanning. |
| **Backwards Compatibility** | ✅ Designed | Each phase maintains existing API contracts. New endpoints are additive. Frontend gracefully handles missing features. |

---

## 13. Recommended Execution Strategy

### Parallel Tracks

Phases 2–4 can be partially parallelized across team members:

```
Week 1─2    Week 2─3    Week 3─4    Week 4─5    Week 5─6    Week 6─7    Week 7─8
┌────────┐  ┌────────┐
│Phase 0 │──│Phase 1 │─┐
│Infra   │  │Auth    │ │
└────────┘  └────────┘ │
                       │  ┌────────────────────────────────────────────┐
                       ├──│ Track A (Backend): Phase 2 → 3 → 4 → 5   │
                       │  └────────────────────────────────────────────┘
                       │  ┌────────────────────────────────────────────┐
                       └──│ Track B (Frontend): Phase 1 → 2 → 4 → 5  │
                          └────────────────────────────────────────────┘
                                                                ┌────────┐
                                                                │Phase 6 │
                                                                │Harden  │
                                                                └────────┘
```

### Phase Exit Criteria

Each phase must satisfy:

1. **Working Deployment** — `docker-compose up` runs all services without errors
2. **Test Coverage** — New unit and integration tests cover all new functionality
3. **Migration Safety** — Alembic migrations apply cleanly (up and down)
4. **API Compatibility** — Existing endpoints maintain their contracts
5. **Documentation** — New endpoints documented in OpenAPI spec
6. **Security Review** — No new secrets in source code; auth checks verified

### Definition of Done (Per Phase)

- [ ] All tasks in the phase completed
- [ ] Unit tests pass (`pytest tests/unit/`)
- [ ] Integration tests pass (`pytest tests/integration/`)
- [ ] Linting passes (`ruff check src/ tests/`)
- [ ] Frontend tests pass (`npm run test`)
- [ ] Frontend linting passes (`npm run lint`)
- [ ] Docker build succeeds (`docker-compose build`)
- [ ] Manual smoke test on `docker-compose up`
- [ ] PR reviewed and approved
- [ ] Documentation updated

---

## Appendix A — Current vs. Target Technology Matrix

| Component | Current | Target | Change Type |
|---|---|---|---|
| **Web Framework** | FastAPI ^0.111.0 | FastAPI ^0.115.8 | Version bump |
| **ASGI Server** | uvicorn ^0.29.0 | uvicorn ^0.34.0 + gunicorn 23.0 | Add process manager |
| **ORM** | sqlalchemy ^2.0.0 (declared, unused) | sqlalchemy[asyncio] ^2.0.38 (active) | Activate existing dep |
| **Async DB Driver** | — | asyncpg ^0.30.0 | New dependency |
| **Sync DB Driver** | — | psycopg2-binary ^2.9.10 | New (Celery + Alembic) |
| **Migrations** | — | alembic ^1.14.1 | New dependency |
| **Password Hashing** | — | pwdlib[argon2] ^0.2.1 | New dependency |
| **JWT** | — | python-jose[cryptography] ^3.3.0 | New dependency |
| **Task Queue** | — | celery[redis] ^5.4.0 | New dependency |
| **Cache / Broker** | — | redis ^5.2.1 | New dependency |
| **SSE** | — | sse-starlette ^2.2.1 | New dependency |
| **Validation** | pydantic ^2.7.0 | pydantic ^2.10.6 | Version bump |
| **Settings** | pydantic-settings ^2.2.0 | pydantic-settings ^2.7.1 | Version bump |
| **Email Validation** | — | email-validator ^2.2.0 | New (for `EmailStr`) |
| **Frontend Framework** | React ^18.3.0 | React ^18.3.0 | No change |
| **Frontend Bundler** | Vite ^5.2.0 | Vite ^6.x | Version bump |
| **Frontend Routing** | — (view state) | react-router-dom ^7.x | New dependency |
| **Frontend HTTP** | axios ^1.7.0 | axios ^1.x | No change |
| **Database** | SQLite (in-memory) | PostgreSQL 16 (Alpine) | New infrastructure |
| **Message Broker** | — | Redis 7 (Alpine) | New infrastructure |
| **Reverse Proxy** | — | Nginx 1.27 (Alpine) | New infrastructure |

---

## Appendix B — Glossary

| Term | Definition |
|---|---|
| **DatabasePort** | Abstract interface (`core/ports/database.py`) defining the contract for read-only database access. All connectors implement this interface. |
| **CleaningEngine** | Application-layer service that normalizes, deduplicates, and type-casts raw database rows into `UniversalRow` format. |
| **UniversalDataType** | Enum abstracting database-specific types into a common set: `TEXT`, `INTEGER`, `FLOAT`, `BOOLEAN`, `TIMESTAMP`, `BINARY`, `UNKNOWN`. |
| **UniversalCell** | Data class representing a single cell with `column` name, `type` (UniversalDataType), and `value`. |
| **UniversalRow** | A list of `UniversalCell` objects representing one row of cleaned data. |
| **ConnectorFactory** | Registry pattern that creates, caches, and manages `DatabasePort` implementations by connection ID. |
| **MetadataIndexer** | Application-layer service that crawls database schemas and builds a searchable index (currently SQLite). |
| **Hexagonal Architecture** | Architectural pattern where the domain core is isolated from external concerns (databases, HTTP, queues) via ports (interfaces) and adapters (implementations). |
| **Dual-Write Progress** | Pattern from TaskFlow where every progress update writes to both a persistent store (PostgreSQL) and a real-time channel (Redis Pub/Sub). |
| **SSE (Server-Sent Events)** | HTTP-based protocol for server-to-client streaming. Used for real-time job progress updates. |
| **JWT (JSON Web Token)** | Compact, URL-safe token for stateless authentication. Encoded with a server-side secret. |
| **Fernet Encryption** | Symmetric encryption scheme (AES-128-CBC + HMAC-SHA256) used to encrypt connection credentials at rest. |
| **Multi-Tenant Isolation** | Design pattern ensuring each user's data is logically separated via `user_id` filtering on every database query. |
| **acks_late** | Celery configuration where task acknowledgment is sent after execution (not before), ensuring crash resilience. |

---

*End of Document*
