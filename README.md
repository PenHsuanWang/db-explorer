# DB Explorer

A local, read-only web application for exploring remote databases. Raw data is fetched and cleaned entirely within the application layer — never at the database layer.

## Quick Start (Docker)

```bash
cp backend/.env.example backend/.env
docker-compose up -d
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/v1

## Manual Dev Setup

### Backend

```bash
cd backend
poetry install
cp .env.example .env
poetry run uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd web-ui
npm install
cp .env.example .env
npm run dev
```

## Architecture

```
React (Vite) → FastAPI → CleaningEngine → DatabasePort → Remote DB
```

- **DatabasePort** — read-only adapters for remote databases (SQLAlchemy, oracledb, clickhouse-driver)
- **CleaningEngine** — normalizes/deduplicates raw rows into `UniversalFormat` in memory (Pandas/Pydantic)
- **API** — returns cleaned JSON to the frontend

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/connections` | List configured DB connections |
| GET | `/api/v1/connections/{id}/tables` | List tables for a connection |
| GET | `/api/v1/connections/{id}/tables/{table}` | Query and return cleaned table data |
