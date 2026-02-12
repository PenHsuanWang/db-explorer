# Project Context: Data Pipeline CLI Tool

## Tech Stack
- **Language:** Python 3.12+
- **CLI Framework:** Typer
- **Configuration:** Pydantic / Pydantic Settings
- **Database:** SQLAlchemy (Core), cx_Oracle, psycopg2
- **Testing:** Pytest, Ruff (Linter)

## Architecture Style
- **Pattern:** Hexagonal / Layered Architecture
- **Key Constraints:**
  - Domain layer (`src/datapipe/domain`) has ZERO external dependencies.
  - Infrastructure depends on Domain.
  - Strict SRP in Inspector module (Checker vs Crawler).

## Commands
- Run app: `python -m src.datapipe.main`
- Run tests: `pytest tests/`
- Lint: `ruff check .`
