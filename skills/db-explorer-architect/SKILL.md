---
name: db-explorer-architect
description: Architect and develop the DB Explorer project with Python backend and React frontend following hexagonal architecture
argument-hint: [component] [task]
---

# Database Explorer Architect

## Goal
Build and maintain a full-stack database exploration tool with:
- **Backend**: Python (FastAPI + hexagonal architecture) for robust, type-safe database connectivity
- **Frontend**: React TypeScript with modern tooling (Vite, Vitest) for responsive UI
- **Architecture**: Hexagonal/Ports & Adapters pattern ensuring clean separation of concerns
- **Databases**: Multi-database support (Oracle, ClickHouse, Databricks) via pluggable adapters

This skill provides comprehensive workflows, coding standards, and tools for developing both backend and frontend components while preserving architectural boundaries.

## Project Structure

```
db-explorer/
├── README.md                      # Project overview and setup
├── docker-compose.yml             # Container orchestration
├── .gitignore                     # Git ignore patterns
├── .pre-commit-config.yaml        # Pre-commit hooks
│
├── backend/                       # Python Backend (FastAPI)
│   ├── pyproject.toml             # Poetry dependencies and config
│   ├── poetry.lock                # Locked dependencies
│   ├── pytest.ini                 # Pytest configuration
│   ├── .env.example               # Environment variables template
│   │
│   ├── src/                       # Source code
│   │   ├── main.py                # FastAPI application entry point
│   │   ├── config.py              # Application configuration
│   │   │
│   │   ├── core/                  # Domain Layer (Pure Python, no external deps)
│   │   │   ├── domain/            # Domain models and types
│   │   │   │   ├── types.py       # UniversalDataType, value objects
│   │   │   │   └── models.py      # Domain entities
│   │   │   └── ports/             # Port interfaces
│   │   │       └── database.py    # DatabasePort interface
│   │   │
│   │   ├── application/           # Application Layer (Use Cases)
│   │   │   ├── query_executor.py  # Query execution service
│   │   │   └── schema_reader.py   # Schema reading service
│   │   │
│   │   └── adapters/              # Adapters Layer (External dependencies)
│   │       ├── driving/           # Driving adapters (API, CLI)
│   │       │   └── api/
│   │       │       └── v1/        # FastAPI routes
│   │       │           ├── queries.py
│   │       │           └── schemas.py
│   │       │
│   │       └── driven/            # Driven adapters (Database connectors)
│   │           ├── oracle.py      # Oracle connector
│   │           ├── clickhouse.py  # ClickHouse connector
│   │           ├── databricks.py  # Databricks connector
│   │           └── factory.py     # Connector factory
│   │
│   └── tests/                     # Test suite
│       ├── conftest.py            # Pytest fixtures
│       ├── unit/                  # Unit tests
│       ├── integration/           # Integration tests
│       └── test_data/             # Test fixtures and data
│
├── web-ui/                        # React TypeScript Frontend
│   ├── package.json               # npm dependencies
│   ├── tsconfig.json              # TypeScript configuration
│   ├── vite.config.ts             # Vite build configuration
│   ├── .env.example               # Environment variables template
│   ├── index.html                 # HTML entry point
│   ├── public/                    # Static assets
│   │
│   └── src/                       # Source code
│       ├── main.tsx               # React entry point
│       ├── App.tsx                # Root component
│       ├── vite-env.d.ts          # Vite type definitions
│       │
│       ├── components/            # React components
│       │   ├── QueryEditor/       # SQL editor component
│       │   ├── SchemaExplorer/    # Schema browser component
│       │   └── ResultsTable/      # Results display component
│       │
│       ├── hooks/                 # Custom React hooks
│       │   ├── useQuery.ts        # Query execution hook
│       │   └── useSchema.ts       # Schema fetching hook
│       │
│       ├── services/              # API service layer
│       │   ├── api.ts             # Axios client setup
│       │   ├── queryService.ts    # Query API calls
│       │   └── schemaService.ts   # Schema API calls
│       │
│       ├── types/                 # TypeScript type definitions
│       │   ├── query.ts           # Query-related types
│       │   └── schema.ts          # Schema-related types
│       │
│       ├── utils/                 # Utility functions
│       └── styles/                # Global styles
│
└── skills/                        # Claude Code skills
    ├── agent-architect/           # General agent skill
    └── db-explorer-architect/     # This skill
        ├── SKILL.md               # Main skill documentation
        ├── scripts/               # Automation scripts
        │   ├── lint_backend.sh    # Backend code quality
        │   └── lint_frontend.sh   # Frontend code quality
        └── references/            # Reference documentation
            ├── architecture.md    # Architecture rules
            ├── design-patterns.md # Design patterns
            ├── python-standards.md # Python coding standards
            └── react-standards.md  # React coding standards
```

## Workflow

### 1. Backend Development (Python)

**Location**: All Python code resides in the `backend/` directory.

**Entry Point**: `backend/src/main.py` - FastAPI application

**Architecture**: Hexagonal (Ports & Adapters)
- **Domain Layer** (`src/core/domain`): Pure Python, zero external dependencies
- **Ports** (`src/core/ports`): Abstract interfaces (e.g., DatabasePort)
- **Application** (`src/application`): Use cases orchestrating domain logic, including the `CleaningEngine`
- **Adapters** (`src/adapters`): External integrations (FastAPI, databases)

**Data Flow** (fetch → clean → serve):
```
API (FastAPI) → DataService → CleaningEngine → DatabasePort → Remote DB
```
- `DatabasePort` fetches **raw, unmodified rows** from the remote database (read-only).
- `CleaningEngine` (`src/application/cleaning_engine.py`) transforms raw rows in memory:
  - **Normalization**: standardize string encoding, trim whitespace, unify `NULL`-like values.
  - **Deduplication**: remove exact-duplicate rows before returning to the API.
  - **Type Casting**: map provider-specific types to `UniversalDataType` values.
- API returns **cleaned, uniformly-formatted JSON** — the frontend always receives a consistent schema.

**Read-Only Enforcement**:
- Every `DatabasePort` implementation **must** use a read-only connection (e.g., `SET TRANSACTION READ ONLY`, `readonly=True` driver option, or a DB user with SELECT-only privileges).
- The `execute_safe_read` method must parse the SQL statement and raise `ReadOnlyViolationError` if it detects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, or `MERGE` keywords before sending the query to the database.

**Adding New Database Connector**:
1. Create adapter: `backend/src/adapters/driven/[db-name].py`
2. Implement `DatabasePort` interface from `src/core/ports/database.py`; enforce read-only mode in `connect()`.
3. Add to factory: `backend/src/adapters/driven/factory.py`
4. Add integration tests: `backend/tests/integration/test_[db-name].py`
5. Update configuration: `backend/src/config.py`

**Code Quality Standards**:
- Formatting: Black (line-length 100)
- Import Sorting: isort (--profile black)
- Type Checking: Mypy (--strict)
- Linting: Ruff
- Testing: Pytest with 80%+ coverage
- Security: Safety check for vulnerabilities

**Configuration**: `backend/pyproject.toml`

**Commands** (run from `backend/` directory):
```bash
# Format code
black src/ tests/ --line-length 100
isort src/ tests/ --profile black

# Type check
mypy src/ --strict

# Lint
ruff check src/ tests/

# Test
pytest tests/ --cov=src --cov-report=term-missing

# All checks
../skills/db-explorer-architect/scripts/lint_backend.sh --fix
```

### 2. Frontend Development (React + TypeScript)

**Location**: All React code resides in the `web-ui/` directory.

**Entry Point**: `web-ui/src/main.tsx` - React application root

**Technology Stack**:
- React 18+ with TypeScript
- Build Tool: Vite
- Testing: Vitest
- HTTP Client: Axios
- Styling: CSS Modules / Tailwind

**Code Quality Standards**:
- Linting: ESLint with React & TypeScript plugins
- Formatting: Prettier (semi, singleQuote, printWidth: 100)
- Type Checking: TypeScript strict mode
- Testing: Vitest with React Testing Library

**Configuration**: `web-ui/tsconfig.json`, `web-ui/vite.config.ts`

**Commands** (run from `web-ui/` directory):
```bash
# Development server
npm run dev

# Lint
npm run lint        # Check
npm run lint:fix    # Auto-fix

# Format
npm run format       # Fix formatting
npm run format:check # Check formatting

# Type check
npm run type-check

# Test
npm run test        # Watch mode
npm run test:run    # Single run

# Build
npm run build

# All checks
../skills/db-explorer-architect/scripts/lint_frontend.sh --fix
```

**Adding New React Component**:
1. Create directory: `web-ui/src/components/[ComponentName]/`
2. Create files:
   - `[ComponentName].tsx` - Component implementation
   - `[ComponentName].module.css` - Styles (optional)
   - `[ComponentName].test.tsx` - Tests
   - `index.ts` - Barrel export
3. Follow component standards (see `references/react-standards.md`)
4. Add tests with React Testing Library

### 3. User Cleaning & View Rules

Users can configure how fetched data is displayed and cleaned **without touching the remote database**. All rules are applied client-side or by the `CleaningEngine` in the backend.

**Supported cleaning / view rules (examples)**:
- **Hide null values**: rows or cells where a value is `NULL` / empty are excluded from the displayed result set.
- **Standardize date format**: all `TIMESTAMP` / date columns are converted to ISO-8601 (`YYYY-MM-DDTHH:mm:ssZ`) before display.
- **Trim whitespace**: leading and trailing whitespace is stripped from string columns.
- **Column aliasing**: users can rename columns in the UI without changing the underlying query.
- **Type override**: force a column to be displayed as a specific `UniversalDataType` when the connector returns an ambiguous type.

**How rules are applied** (backend flow):
1. The API receives a `CleaningConfig` alongside the SQL query.
2. `DataService` forwards raw rows from `DatabasePort` to `CleaningEngine.apply(rows, config)`.
3. `CleaningEngine` applies each enabled rule in order and returns the cleaned `List[UniversalRow]`.
4. The API serialises the result to JSON and returns it to the frontend.

**Frontend contract**: the frontend always receives a `UniversalFormat` response — a list of objects with `{ column: string, type: UniversalDataType, value: any }` entries — regardless of the source database.

### 4. Integration & Deployment

**Docker Setup**:
- File: `docker-compose.yml` at project root
- Services: backend (FastAPI), frontend (Nginx/Vite), databases (dev)

**Environment Configuration**:
- Backend: `backend/.env` (copied from `.env.example`)
  ```bash
  DATABASE_URL=oracle://user:pass@host:port/service
  LOG_LEVEL=INFO
  CORS_ORIGINS=http://localhost:5173
  ```
- Frontend: `web-ui/.env` (copied from `.env.example`)
  ```bash
  VITE_API_BASE_URL=http://localhost:8000/api/v1
  ```

**API Communication**:
- Frontend calls backend at `http://localhost:8000/api/v1`
- CORS configured in `backend/src/main.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:5173"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

**Deployment**:
```bash
# Development
docker-compose up -d

# Backend only
cd backend && uvicorn src.main:app --reload

# Frontend only
cd web-ui && npm run dev
```

## Code Quality Standards

### Backend (Python)
- **Formatting**: Black with line-length 100
- **Import Sorting**: isort with --profile black
- **Type Checking**: Mypy with --strict mode
- **Linting**: Ruff for fast, comprehensive checks
- **Testing**: Pytest with 80%+ coverage
- **Security**: Safety check for dependency vulnerabilities
- **Documentation**: Google-style docstrings (PEP 257)

See `references/python-standards.md` for complete Python coding standards.

### Frontend (React + TypeScript)
- **Formatting**: Prettier (semi, singleQuote, printWidth: 100)
- **Linting**: ESLint with React, TypeScript, and accessibility plugins
- **Type Checking**: TypeScript strict mode
- **Testing**: Vitest with React Testing Library
- **Component Structure**: Feature-based organization with colocated tests
- **Naming**: PascalCase for components, camelCase for functions

See `references/react-standards.md` for complete React/TypeScript coding standards.

## Design Patterns

### Backend Patterns
- **Hexagonal Architecture**: Ports & Adapters for clean separation
- **Factory Pattern**: Connector creation via ConnectorFactory
- **Adapter Pattern**: Database-specific implementations of DatabasePort
- **Strategy Pattern**: Pluggable query execution strategies
- **Iterator Pattern**: Streaming query results with generators

### Frontend Patterns
- **Component Composition**: Reusable, composable React components
- **Custom Hooks**: Encapsulate stateful logic (useQuery, useSchema)
- **Service Layer**: Centralized API communication
- **Context API**: Global state management (auth, theme)
- **Error Boundaries**: Graceful error handling

See `references/design-patterns.md` for detailed pattern implementations.

## Scripts

### Backend Scripts
- **`scripts/lint_backend.sh`**: Run all backend quality checks
  ```bash
  ./skills/db-explorer-architect/scripts/lint_backend.sh [--fix]
  ```
  Runs: Black, isort, Mypy, Ruff, Pytest

### Frontend Scripts
- **`scripts/lint_frontend.sh`**: Run all frontend quality checks
  ```bash
  ./skills/db-explorer-architect/scripts/lint_frontend.sh [--fix]
  ```
  Runs: Prettier, ESLint, TypeScript check, Vitest

### Combined Scripts
- **`scripts/test_all.sh`**: Run all tests (backend + frontend)
- **`scripts/docker_dev.sh`**: Start development environment with Docker

## References

Comprehensive documentation for architecture, patterns, and coding standards:

- **`references/architecture.md`**: Hexagonal architecture rules, layer dependencies, DatabasePort interface contract, streaming & transport requirements, security & secrets management
- **`references/python-standards.md`**: Python coding standards including:
  - Code style, formatting, and linting (Black, isort, Ruff)
  - Type hinting best practices (PEP 484, 585, 604)
  - Google-style docstrings (PEP 257)
  - Error handling and SOLID principles
  - Testing requirements (pytest, 80% coverage)
  - Performance, security, and logging standards
- **`references/react-standards.md`**: React/TypeScript coding standards including:
  - TypeScript strict mode configuration
  - Component structure and organization
  - Custom hooks best practices
  - API service layer patterns
  - Testing with Vitest and React Testing Library
  - Performance optimization (memoization, code splitting)
  - Accessibility guidelines
- **`references/design-patterns.md`**: Design pattern implementations:
  - Creational: Factory, Builder
  - Structural: Adapter, Decorator
  - Behavioral: Strategy, Iterator, Observer

## Development Workflow

### Adding a New Database Connector

1. **Create Adapter** (`backend/src/adapters/driven/[db-name].py`):
   ```python
   from src.core.ports.database import DatabasePort
   
   class MyDBConnector(DatabasePort):
       def connect(self) -> None: ...
       def execute_query_stream(self, sql: str, params=None): ...
       def fetch_schema(self, table: str): ...
   ```

2. **Register in Factory** (`backend/src/adapters/driven/factory.py`):
   ```python
   CONNECTORS = {
       "mydb": MyDBConnector,
       # ... other connectors
   }
   ```

3. **Add Configuration** (`backend/src/config.py`):
   ```python
   class MyDBConfig(BaseModel):
       host: str
       port: int = 5432
       database: str
   ```

4. **Write Tests** (`backend/tests/integration/test_mydb.py`):
   ```python
   def test_mydb_connection():
       connector = MyDBConnector(config)
       connector.connect()
       assert connector.is_connected()
   ```

### Adding a New API Endpoint

1. **Define Route** (`backend/src/adapters/driving/api/v1/[resource].py`):
   ```python
   @router.post("/queries/execute")
   async def execute_query(request: QueryRequest):
       result = query_executor.execute(request.sql)
       return {"data": result}
   ```

2. **Frontend Service** (`web-ui/src/services/queryService.ts`):
   ```typescript
   export const executeQuery = async (sql: string): Promise<QueryResult> => {
       const response = await api.post('/queries/execute', { sql });
       return response.data;
   };
   ```

3. **React Hook** (`web-ui/src/hooks/useQuery.ts`):
   ```typescript
   export const useQuery = () => {
       const [data, setData] = useState<QueryResult | null>(null);
       const execute = useCallback(async (sql: string) => {
           const result = await executeQuery(sql);
           setData(result);
       }, []);
       return { data, execute };
   };
   ```

### Adding a New React Component

1. **Create Component Directory**:
   ```
   web-ui/src/components/MyComponent/
   ├── MyComponent.tsx
   ├── MyComponent.module.css
   ├── MyComponent.test.tsx
   └── index.ts
   ```

2. **Implement Component** (`MyComponent.tsx`):
   ```typescript
   import React from 'react';
   import styles from './MyComponent.module.css';
   
   interface MyComponentProps {
       title: string;
       onAction: () => void;
   }
   
   export const MyComponent: React.FC<MyComponentProps> = ({ title, onAction }) => {
       return (
           <div className={styles.container}>
               <h2>{title}</h2>
               <button onClick={onAction}>Action</button>
           </div>
       );
   };
   ```

3. **Add Tests** (`MyComponent.test.tsx`):
   ```typescript
   import { render, screen, fireEvent } from '@testing-library/react';
   import { MyComponent } from './MyComponent';
   
   describe('MyComponent', () => {
       it('calls onAction when button clicked', () => {
           const mockAction = vi.fn();
           render(<MyComponent title="Test" onAction={mockAction} />);
           fireEvent.click(screen.getByRole('button'));
           expect(mockAction).toHaveBeenCalled();
       });
   });
   ```

## Environment Variables

### Backend (.env)
```bash
# Database Configuration
DATABASE_URL=oracle://user:password@host:1521/service
CLICKHOUSE_URL=http://localhost:8123
DATABRICKS_HOST=your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
SECRET_KEY=your-secret-key

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Security
MAX_QUERY_ROWS=10000
QUERY_TIMEOUT_SECONDS=300
```

### Frontend (.env)
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Feature Flags
VITE_ENABLE_QUERY_HISTORY=true
VITE_ENABLE_SCHEMA_EXPLORER=true

# Application Configuration
VITE_APP_TITLE=DB Explorer
VITE_MAX_RESULT_ROWS=1000
```

## Quick Start

### Initial Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/your-org/db-explorer.git
   cd db-explorer
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   
   # Install Python 3.12+
   # Install Poetry: https://python-poetry.org/docs/#installation
   
   poetry install
   cp .env.example .env
   # Edit .env with your database credentials
   
   # Run migrations (if applicable)
   poetry run alembic upgrade head
   
   # Start backend server
   poetry run uvicorn src.main:app --reload
   ```

3. **Frontend Setup**:
   ```bash
   cd web-ui
   
   # Install Node.js 18+ and npm
   
   npm install
   cp .env.example .env
   # Edit .env with your API URL
   
   # Start development server
   npm run dev
   ```

4. **Access Application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Development Workflow

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**: Follow coding standards for backend or frontend

3. **Run Quality Checks**:
   ```bash
   # Backend
   cd backend
   ../skills/db-explorer-architect/scripts/lint_backend.sh --fix
   
   # Frontend
   cd web-ui
   ../skills/db-explorer-architect/scripts/lint_frontend.sh --fix
   ```

4. **Run Tests**:
   ```bash
   # Backend
   cd backend && pytest tests/ -v
   
   # Frontend
   cd web-ui && npm run test:run
   ```

5. **Commit and Push**:
   ```bash
   git add .
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**: Follow PR template guidelines


