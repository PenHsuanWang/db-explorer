---
name: python-backend-dev
description: Comprehensive Python backend development guide with CI/CD workflows, testing, documentation, and best practices using uv, flake8, mypy, pytest, and Sphinx.
argument-hint: [task: setup-project | run-tests | build-docs | lint]
claude-skill-version: 1.0
---

# Python Backend Development Skill Guide

## Goal

This skill guide provides production-ready workflows, CI/CD pipelines, testing strategies, and documentation standards for Python backend development. It covers modern Python tooling including uv package management, flake8 linting, mypy type checking, pytest testing, and Sphinx documentation generation.

## Intended Audience

Backend developers working on Python projects who need:
- Production-ready CI/CD workflows
- Comprehensive testing and type checking
- API documentation generation
- Modern package management with uv
- Best practices for maintainable, type-safe code

## 1. CI/CD Workflows

### 1.1 Linting with flake8

**Purpose**: Enforce code style following PEP 8 standards

**Configuration** (`.flake8`):
```ini
[flake8]
max-line-length = 100
ignore = E203, E266, E501, W503
max-complexity = 10
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .venv,
    venv,
    .eggs,
    *.egg-info
```

**Run Command**:
```bash
flake8 src/ tests/
```

**CI Integration**: See complete workflow in section 4.1

### 1.2 Type Checking with mypy

**Purpose**: Static type analysis for type safety

**Configuration** (in `pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_reexport = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
```

**Run Command**:
```bash
mypy src/
```

**CI Integration**: See complete workflow in section 4.1

### 1.3 Unit Testing with pytest

**Purpose**: Comprehensive test coverage with detailed reporting

**Configuration** (in `pyproject.toml`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "--cov=src",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "--junitxml=test-results/junit.xml",
    "-v"
]
```

**Run Command**:
```bash
pytest tests/
```

**CI Integration**: See complete workflow in section 4.1

### 1.4 Documentation Building with Sphinx

**Purpose**: Generate API documentation with GitHub Pages deployment

**Initial Setup**:
```bash
# Install Sphinx
uv add --dev sphinx sphinx-rtd-theme

# Initialize Sphinx
cd docs
sphinx-quickstart --quiet --project="My Project" --author="Your Name" -v "1.0"
```

**Build Command**:
```bash
sphinx-build -b html docs/source docs/build/html
```

**CI Integration**: See complete workflow in section 4.2

## 2. UV Package Management

### 2.1 Project Initialization

```bash
# Initialize new project
uv init my-project
cd my-project

# Initialize in existing directory
uv init
```

### 2.2 Dependency Management

```bash
# Add production dependency
uv add requests

# Add development dependency
uv add --dev pytest pytest-cov

# Add specific version
uv add "fastapi==0.109.0"

# Install all dependencies
uv sync

# Update dependencies
uv lock --upgrade
```

### 2.3 Lock Files

uv automatically manages `uv.lock` file for reproducible builds:
- Contains exact versions of all dependencies
- Committed to version control
- Ensures consistent environments

### 2.4 Build and Packaging

```bash
# Build distribution packages
uv build

# Creates:
# - dist/*.whl (wheel)
# - dist/*.tar.gz (source distribution)
```

### 2.5 Complete pyproject.toml Configuration

```toml
[project]
name = "my-backend-project"
version = "1.0.0"
description = "A production-ready Python backend"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "sqlalchemy>=2.0.25",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.4",
    "pytest-cov>=4.1.0",
    "flake8>=7.0.0",
    "mypy>=1.8.0",
    "sphinx>=7.2.6",
    "sphinx-rtd-theme>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.4",
    "pytest-cov>=4.1.0",
    "flake8>=7.0.0",
    "mypy>=1.8.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "--cov=src",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "--junitxml=test-results/junit.xml",
    "-v"
]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_reexport = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/site-packages/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

## 3. Type Hints & reStructuredText Docstrings

### 3.1 Type Hints with typing Module

```python
from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import datetime

def process_user_data(
    user_id: int,
    username: str,
    email: Optional[str] = None,
    tags: List[str] = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Union[str, int, List[str]]]:
    """
    Process user data and return formatted result.
    
    :param user_id: Unique identifier for the user
    :type user_id: int
    :param username: Username for the account
    :type username: str
    :param email: Optional email address
    :type email: Optional[str]
    :param tags: List of user tags
    :type tags: Optional[List[str]]
    :param metadata: Additional metadata dictionary
    :type metadata: Optional[Dict[str, Any]]
    
    :return: Formatted user data dictionary
    :rtype: Dict[str, Union[str, int, List[str]]]
    
    :raises ValueError: If user_id is negative
    :raises TypeError: If username is not a string
    
    .. note::
       This function validates all input parameters before processing.
    
    .. warning::
       Large metadata dictionaries may impact performance.
    
    .. seealso::
       :func:`validate_user_data` for validation logic
    
    **Example Usage:**
    
    .. code-block:: python
    
        result = process_user_data(
            user_id=123,
            username="john_doe",
            email="john@example.com",
            tags=["admin", "verified"]
        )
        print(result)
        # {'id': 123, 'name': 'john_doe', 'email': 'john@example.com', 'tags': ['admin', 'verified']}
    """
    if user_id < 0:
        raise ValueError("user_id must be non-negative")
    if not isinstance(username, str):
        raise TypeError("username must be a string")
    
    tags = tags or []
    metadata = metadata or {}
    
    return {
        "id": user_id,
        "name": username,
        "email": email or "not_provided",
        "tags": tags,
    }
```

### 3.2 Class Documentation with Instance Variables

```python
from typing import Optional, List
from datetime import datetime

class DatabaseConnection:
    """
    Manages database connection lifecycle with context manager support.
    
    This class provides a robust connection manager with automatic resource
    cleanup and error handling.
    
    :ivar host: Database host address
    :vartype host: str
    :ivar port: Database port number
    :vartype port: int
    :ivar database: Database name
    :vartype database: str
    :ivar connected: Connection status flag
    :vartype connected: bool
    :ivar connection_time: Timestamp of last connection
    :vartype connection_time: Optional[datetime]
    
    .. note::
       Always use this class as a context manager to ensure proper cleanup.
    
    .. warning::
       Connections are not thread-safe. Create separate instances per thread.
    
    **Example Usage:**
    
    .. code-block:: python
    
        with DatabaseConnection("localhost", 5432, "mydb") as conn:
            result = conn.execute("SELECT * FROM users")
            print(result)
    """
    
    def __init__(self, host: str, port: int, database: str) -> None:
        """
        Initialize database connection parameters.
        
        :param host: Database server hostname or IP
        :type host: str
        :param port: Database server port
        :type port: int
        :param database: Target database name
        :type database: str
        
        :raises ValueError: If port is not in valid range (1-65535)
        """
        if not 1 <= port <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        
        self.host: str = host
        self.port: int = port
        self.database: str = database
        self.connected: bool = False
        self.connection_time: Optional[datetime] = None
    
    def __enter__(self) -> "DatabaseConnection":
        """
        Enter context manager and establish connection.
        
        :return: The connection instance
        :rtype: DatabaseConnection
        
        :raises ConnectionError: If connection fails
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit context manager and close connection.
        
        :param exc_type: Exception type if raised
        :param exc_val: Exception value if raised
        :param exc_tb: Exception traceback if raised
        
        :return: False to propagate exceptions
        :rtype: bool
        """
        self.disconnect()
        return False
    
    def connect(self) -> None:
        """
        Establish database connection.
        
        :raises ConnectionError: If connection cannot be established
        
        .. note::
           Connection parameters are validated before attempting connection.
        """
        # Connection logic here
        self.connected = True
        self.connection_time = datetime.now()
    
    def disconnect(self) -> None:
        """
        Close database connection and cleanup resources.
        
        .. note::
           Safe to call multiple times - idempotent operation.
        """
        if self.connected:
            # Cleanup logic here
            self.connected = False
    
    def execute(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.
        
        :param query: SQL query string
        :type query: str
        
        :return: List of result dictionaries
        :rtype: List[Dict[str, Any]]
        
        :raises RuntimeError: If not connected
        :raises ValueError: If query is empty
        
        .. warning::
           This method does not provide SQL injection protection.
           Use parameterized queries in production.
        """
        if not self.connected:
            raise RuntimeError("Not connected to database")
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Query execution logic here
        return []
```

## 4. Complete GitHub Actions Workflows

### 4.1 CI Workflow (.github/workflows/ci.yml)

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint-and-type-check:
    name: Lint and Type Check
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install uv
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: |
          uv sync --dev
      
      - name: Run flake8
        run: |
          uv run flake8 src/ tests/
      
      - name: Run mypy
        run: |
          uv run mypy src/
  
  test:
    name: Test Suite
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install uv
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: |
          uv sync --dev
      
      - name: Run pytest
        run: |
          uv run pytest tests/ --cov=src --cov-report=xml --cov-report=html --cov-report=term-missing --junitxml=test-results/junit.xml
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.python-version }}
          path: test-results/
      
      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report-${{ matrix.python-version }}
          path: htmlcov/
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-${{ matrix.python-version }}
          fail_ci_if_error: false
  
  build:
    name: Build Package
    runs-on: ubuntu-latest
    needs: [lint-and-type-check, test]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Install uv
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH
      
      - name: Build package
        run: |
          uv build
      
      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist-packages
          path: dist/
```

### 4.2 Documentation Workflow (.github/workflows/docs.yml)

```yaml
name: Documentation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-docs:
    name: Build Documentation
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Install uv
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: |
          uv sync --dev
          uv add --dev sphinx sphinx-rtd-theme
      
      - name: Generate API documentation
        run: |
          uv run sphinx-apidoc -f -o docs/source/api src/
      
      - name: Build Sphinx documentation
        run: |
          uv run sphinx-build -b html docs/source docs/build/html
      
      - name: Upload documentation artifact
        uses: actions/upload-artifact@v4
        with:
          name: documentation
          path: docs/build/html/
      
      - name: Deploy to GitHub Pages
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/build/html
```

## 5. Testing with pytest

### 5.1 Unit Test Structure

**tests/test_user_service.py**:
```python
import pytest
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from src.services.user_service import UserService, User


class TestUserService:
    """Test suite for UserService class."""
    
    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.service = UserService()
    
    def teardown_method(self) -> None:
        """Clean up after each test method."""
        self.service = None
    
    def test_create_user_success(self) -> None:
        """Test successful user creation."""
        user = self.service.create_user(
            username="testuser",
            email="test@example.com"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.id is not None
    
    def test_create_user_duplicate_username(self) -> None:
        """Test that duplicate usernames raise ValueError."""
        self.service.create_user(username="testuser", email="test1@example.com")
        
        with pytest.raises(ValueError, match="Username already exists"):
            self.service.create_user(username="testuser", email="test2@example.com")
    
    @pytest.mark.parametrize("username,email,expected_error", [
        ("", "test@example.com", "Username cannot be empty"),
        ("testuser", "", "Email cannot be empty"),
        ("ab", "test@example.com", "Username must be at least 3 characters"),
        ("testuser", "invalid-email", "Invalid email format"),
    ])
    def test_create_user_validation_errors(
        self,
        username: str,
        email: str,
        expected_error: str
    ) -> None:
        """Test user creation validation with various invalid inputs."""
        with pytest.raises(ValueError, match=expected_error):
            self.service.create_user(username=username, email=email)
    
    def test_get_user_by_id_found(self) -> None:
        """Test retrieving an existing user by ID."""
        created_user = self.service.create_user(
            username="testuser",
            email="test@example.com"
        )
        
        retrieved_user = self.service.get_user_by_id(created_user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == created_user.username
    
    def test_get_user_by_id_not_found(self) -> None:
        """Test retrieving a non-existent user returns None."""
        user = self.service.get_user_by_id(99999)
        assert user is None
    
    @patch('src.services.user_service.send_email')
    def test_create_user_sends_welcome_email(self, mock_send_email: Mock) -> None:
        """Test that user creation triggers welcome email."""
        user = self.service.create_user(
            username="testuser",
            email="test@example.com"
        )
        
        mock_send_email.assert_called_once_with(
            to=user.email,
            subject="Welcome!",
            body=pytest.approx("Welcome testuser", rel=1e-3)
        )
```

### 5.2 Fixtures with conftest.py

**tests/conftest.py**:
```python
import pytest
from typing import Generator
from src.database import Database
from src.services.user_service import UserService


@pytest.fixture
def database() -> Generator[Database, None, None]:
    """
    Provide a test database instance.
    
    Yields:
        Database: A configured test database instance
    """
    db = Database(url="sqlite:///:memory:")
    db.create_tables()
    yield db
    db.drop_tables()
    db.close()


@pytest.fixture
def user_service(database: Database) -> UserService:
    """
    Provide a UserService instance with test database.
    
    Args:
        database: Test database fixture
    
    Returns:
        UserService: Configured service instance
    """
    return UserService(database=database)


@pytest.fixture
def sample_users() -> List[Dict[str, str]]:
    """
    Provide sample user data for testing.
    
    Returns:
        List of user dictionaries
    """
    return [
        {"username": "user1", "email": "user1@example.com"},
        {"username": "user2", "email": "user2@example.com"},
        {"username": "user3", "email": "user3@example.com"},
    ]
```

### 5.3 Coverage Configuration

Coverage settings are in `pyproject.toml` (see section 2.5).

**Verify Coverage**:
```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Open HTML report
open htmlcov/index.html
```

## 6. Sphinx Documentation

### 6.1 Installation and Setup

```bash
# Add Sphinx dependencies
uv add --dev sphinx sphinx-rtd-theme

# Create docs directory
mkdir -p docs/source

# Initialize Sphinx (or create manually)
cd docs
sphinx-quickstart --quiet --project="My Backend" --author="Your Name" -v "1.0"
```

### 6.2 Sphinx Configuration (docs/source/conf.py)

```python
# Configuration file for the Sphinx documentation builder.

import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------
project = 'My Backend Project'
copyright = '2026, Your Name'
author = 'Your Name'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master', None),
}

# Todo extension
todo_include_todos = True
```

### 6.3 Index Structure (docs/source/index.rst)

```rst
Welcome to My Backend Project Documentation
===========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api/modules
   examples
   changelog

Overview
--------

This is a comprehensive Python backend project with full CI/CD integration,
type safety, and extensive documentation.

Features
--------

* **Type-Safe**: Full mypy strict mode compliance
* **Well-Tested**: >80% code coverage with pytest
* **CI/CD Ready**: GitHub Actions workflows included
* **API Documentation**: Auto-generated with Sphinx

Quick Start
-----------

Install the package:

.. code-block:: bash

   pip install my-backend-project

Basic usage:

.. code-block:: python

   from my_backend import UserService

   service = UserService()
   user = service.create_user("john_doe", "john@example.com")
   print(user)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
```

### 6.4 API Documentation Auto-Generation

```bash
# Generate API documentation from source code
sphinx-apidoc -f -o docs/source/api src/

# Build HTML documentation
sphinx-build -b html docs/source docs/build/html

# View documentation
open docs/build/html/index.html
```

### 6.5 GitHub Pages Deployment

Documentation is automatically deployed via the workflow in section 4.2. To enable GitHub Pages:

1. Go to repository Settings → Pages
2. Set Source to "GitHub Actions"
3. Documentation will be available at `https://<username>.github.io/<repo>/`

## 7. Configuration Files

### 7.1 .flake8 Configuration

```ini
[flake8]
max-line-length = 100
ignore = E203, E266, E501, W503
max-complexity = 10
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .venv,
    venv,
    .eggs,
    *.egg-info,
    .tox,
    .pytest_cache
per-file-ignores =
    __init__.py:F401
```

**Explanation**:
- `E203`: Whitespace before ':' (conflicts with Black)
- `E266`: Too many leading '#' for block comment
- `E501`: Line too long (handled by max-line-length)
- `W503`: Line break before binary operator (conflicts with PEP 8 update)
- `max-complexity`: McCabe complexity threshold

### 7.2 Complete pyproject.toml

See section 2.5 for the complete configuration file including:
- Project metadata
- Dependencies
- pytest configuration
- mypy configuration
- coverage configuration

## 8. Comprehensive Code Examples

### 8.1 Type-Hinted Service Layer

```python
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class User:
    """
    User domain model.
    
    :ivar id: Unique user identifier
    :vartype id: int
    :ivar username: User's username
    :vartype username: str
    :ivar email: User's email address
    :vartype email: str
    :ivar created_at: Account creation timestamp
    :vartype created_at: datetime
    """
    id: int
    username: str
    email: str
    created_at: datetime


class UserRepository:
    """
    Repository for user data access.
    
    Handles all database operations for User entities.
    
    .. note::
       This repository uses connection pooling for efficiency.
    """
    
    def __init__(self, connection_string: str) -> None:
        """
        Initialize repository with database connection.
        
        :param connection_string: Database connection URL
        :type connection_string: str
        """
        self.connection_string = connection_string
        self.users: Dict[int, User] = {}
        self.next_id: int = 1
    
    def create(self, username: str, email: str) -> User:
        """
        Create a new user.
        
        :param username: Desired username
        :type username: str
        :param email: User email address
        :type email: str
        
        :return: Created user instance
        :rtype: User
        
        :raises ValueError: If username or email is invalid
        """
        user = User(
            id=self.next_id,
            username=username,
            email=email,
            created_at=datetime.now()
        )
        self.users[self.next_id] = user
        self.next_id += 1
        return user
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """
        Find user by ID.
        
        :param user_id: User identifier
        :type user_id: int
        
        :return: User if found, None otherwise
        :rtype: Optional[User]
        """
        return self.users.get(user_id)
    
    def find_all(self) -> List[User]:
        """
        Retrieve all users.
        
        :return: List of all users
        :rtype: List[User]
        """
        return list(self.users.values())
```

### 8.2 Context Manager Implementation

```python
from typing import Optional
from contextlib import contextmanager


class TransactionManager:
    """
    Manages database transactions with context manager support.
    
    :ivar connection: Database connection instance
    :vartype connection: Any
    :ivar in_transaction: Transaction active flag
    :vartype in_transaction: bool
    
    .. warning::
       Nested transactions are not supported.
    
    **Example Usage:**
    
    .. code-block:: python
    
        with TransactionManager(conn) as txn:
            txn.execute("INSERT INTO users VALUES (...)")
            txn.execute("UPDATE accounts SET balance = ...")
            # Automatically commits on success, rolls back on exception
    """
    
    def __init__(self, connection: Any) -> None:
        """
        Initialize transaction manager.
        
        :param connection: Database connection
        :type connection: Any
        """
        self.connection = connection
        self.in_transaction: bool = False
    
    def __enter__(self) -> "TransactionManager":
        """
        Begin transaction.
        
        :return: Transaction manager instance
        :rtype: TransactionManager
        
        :raises RuntimeError: If already in transaction
        """
        if self.in_transaction:
            raise RuntimeError("Already in transaction")
        
        self.connection.begin()
        self.in_transaction = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Commit or rollback transaction.
        
        :param exc_type: Exception type if raised
        :param exc_val: Exception value if raised
        :param exc_tb: Exception traceback if raised
        
        :return: False to propagate exceptions
        :rtype: bool
        """
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        
        self.in_transaction = False
        return False
    
    def execute(self, query: str) -> Any:
        """
        Execute SQL query within transaction.
        
        :param query: SQL query string
        :type query: str
        
        :return: Query result
        :rtype: Any
        
        :raises RuntimeError: If not in transaction
        """
        if not self.in_transaction:
            raise RuntimeError("Not in transaction")
        
        return self.connection.execute(query)
```

### 8.3 Comprehensive Test Suite

```python
import pytest
from typing import List
from unittest.mock import Mock, patch, MagicMock

from src.services.user_service import UserService, User
from src.repositories.user_repository import UserRepository


class TestUserRepository:
    """Test suite for UserRepository."""
    
    @pytest.fixture
    def repository(self) -> UserRepository:
        """Provide a test repository instance."""
        return UserRepository("sqlite:///:memory:")
    
    def test_create_user(self, repository: UserRepository) -> None:
        """Test user creation."""
        user = repository.create("testuser", "test@example.com")
        
        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_find_by_id_exists(self, repository: UserRepository) -> None:
        """Test finding existing user."""
        created = repository.create("testuser", "test@example.com")
        found = repository.find_by_id(created.id)
        
        assert found is not None
        assert found.id == created.id
    
    def test_find_by_id_not_exists(self, repository: UserRepository) -> None:
        """Test finding non-existent user."""
        found = repository.find_by_id(999)
        assert found is None
    
    @pytest.mark.parametrize("username,email", [
        ("user1", "user1@example.com"),
        ("user2", "user2@example.com"),
        ("user3", "user3@example.com"),
    ])
    def test_create_multiple_users(
        self,
        repository: UserRepository,
        username: str,
        email: str
    ) -> None:
        """Test creating multiple users with different data."""
        user = repository.create(username, email)
        assert user.username == username
        assert user.email == email


class TestTransactionManager:
    """Test suite for TransactionManager."""
    
    @pytest.fixture
    def mock_connection(self) -> Mock:
        """Provide a mock database connection."""
        connection = Mock()
        connection.begin = Mock()
        connection.commit = Mock()
        connection.rollback = Mock()
        connection.execute = Mock(return_value="result")
        return connection
    
    def test_successful_transaction(self, mock_connection: Mock) -> None:
        """Test successful transaction commits."""
        from src.transaction import TransactionManager
        
        with TransactionManager(mock_connection) as txn:
            result = txn.execute("SELECT * FROM users")
        
        mock_connection.begin.assert_called_once()
        mock_connection.commit.assert_called_once()
        mock_connection.rollback.assert_not_called()
        assert result == "result"
    
    def test_failed_transaction_rollback(self, mock_connection: Mock) -> None:
        """Test failed transaction rolls back."""
        from src.transaction import TransactionManager
        
        with pytest.raises(ValueError):
            with TransactionManager(mock_connection) as txn:
                txn.execute("INSERT INTO users VALUES (...)")
                raise ValueError("Simulated error")
        
        mock_connection.begin.assert_called_once()
        mock_connection.rollback.assert_called_once()
        mock_connection.commit.assert_not_called()
    
    def test_nested_transaction_raises(self, mock_connection: Mock) -> None:
        """Test that nested transactions are not allowed."""
        from src.transaction import TransactionManager
        
        txn = TransactionManager(mock_connection)
        
        with txn:
            with pytest.raises(RuntimeError, match="Already in transaction"):
                with txn:
                    pass
```

## 9. Best Practices

### 9.1 Type Hint Guidelines (PEP 484)

**Do:**
- ✅ Use type hints for all function parameters and return types
- ✅ Import types from `typing` module: `Optional`, `List`, `Dict`, `Union`
- ✅ Use `None` as return type for functions without return value
- ✅ Use `-> None` instead of omitting return type
- ✅ Use `Optional[T]` for nullable types
- ✅ Use `Union[T1, T2]` for multi-type parameters

**Don't:**
- ❌ Skip type hints on public APIs
- ❌ Use `Any` unless absolutely necessary
- ❌ Use mutable default arguments (`list=[]`)
- ❌ Mix typing styles (e.g., `list[str]` vs `List[str]`)

### 9.2 Docstring Standards (PEP 257, reStructuredText)

**Do:**
- ✅ Use reStructuredText format for all docstrings
- ✅ Include `:param:`, `:type:`, `:return:`, `:rtype:`, `:raises:`
- ✅ Document all parameters, including optional ones
- ✅ Use Sphinx directives: `.. note::`, `.. warning::`, `.. seealso::`
- ✅ Include usage examples in docstrings
- ✅ Document class instance variables with `:ivar:` and `:vartype:`

**Don't:**
- ❌ Leave public APIs undocumented
- ❌ Use inconsistent docstring formats
- ❌ Forget to document exceptions
- ❌ Skip examples for complex APIs

### 9.3 Testing Strategies

**Do:**
- ✅ Aim for >80% code coverage
- ✅ Test edge cases and error conditions
- ✅ Use parametrized tests for multiple inputs
- ✅ Mock external dependencies
- ✅ Organize tests in classes by component
- ✅ Use descriptive test names: `test_<method>_<scenario>_<expected_result>`
- ✅ Use fixtures for shared setup

**Don't:**
- ❌ Test implementation details
- ❌ Have tests dependent on execution order
- ❌ Skip testing error paths
- ❌ Write tests without assertions

### 9.4 Code Quality Rules (PEP 8)

**Do:**
- ✅ Follow PEP 8 style guide
- ✅ Keep line length ≤100 characters
- ✅ Keep cyclomatic complexity ≤10
- ✅ Use meaningful variable names
- ✅ Group imports: stdlib, third-party, local
- ✅ Use 4 spaces for indentation

**Don't:**
- ❌ Use wildcard imports (`from module import *`)
- ❌ Create functions with >50 lines
- ❌ Use single-letter variables (except loop counters)
- ❌ Ignore linter warnings

### 9.5 Dependency Management with uv

**Do:**
- ✅ Commit `uv.lock` to version control
- ✅ Use exact versions for production dependencies
- ✅ Separate dev dependencies with `--dev` flag
- ✅ Run `uv sync` after pulling changes
- ✅ Update lock file regularly with `uv lock --upgrade`

**Don't:**
- ❌ Manually edit `uv.lock`
- ❌ Use `pip` alongside `uv` in the same project
- ❌ Forget to update lock file after adding dependencies

## 10. Official Documentation References

### Core Tools
- ✅ **uv**: https://docs.astral.sh/uv/
- ✅ **flake8**: https://flake8.pycqa.org/en/latest/
- ✅ **mypy**: https://mypy.readthedocs.io/en/stable/
- ✅ **pytest**: https://docs.pytest.org/en/stable/
- ✅ **Sphinx**: https://www.sphinx-doc.org/en/master/

### Documentation Standards
- ✅ **reStructuredText**: https://docutils.sourceforge.io/rst.html
- ✅ **Sphinx reStructuredText Primer**: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
- ✅ **Napoleon Extension**: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html

### Python Standards
- ✅ **PEP 8** (Style Guide): https://peps.python.org/pep-0008/
- ✅ **PEP 257** (Docstring Conventions): https://peps.python.org/pep-0257/
- ✅ **PEP 484** (Type Hints): https://peps.python.org/pep-0484/

### CI/CD
- ✅ **GitHub Actions Python**: https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python
- ✅ **Codecov**: https://docs.codecov.com/docs

### Additional Resources
- **Python Packaging**: https://packaging.python.org/
- **Type Checking**: https://typing.readthedocs.io/
- **Testing Best Practices**: https://docs.pytest.org/en/stable/goodpractices.html

## 11. Quick Reference Commands

### Project Setup
```bash
# Initialize new project
uv init my-project
cd my-project

# Add dependencies
uv add fastapi uvicorn sqlalchemy pydantic

# Add dev dependencies
uv add --dev pytest pytest-cov flake8 mypy sphinx sphinx-rtd-theme

# Install all dependencies
uv sync
```

### Code Quality Checks
```bash
# Run flake8
flake8 src/ tests/

# Run mypy
mypy src/

# Run both
flake8 src/ tests/ && mypy src/
```

### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_user_service.py

# Run specific test
pytest tests/test_user_service.py::TestUserService::test_create_user

# Run with verbose output
pytest tests/ -v

# Run and stop on first failure
pytest tests/ -x
```

### Documentation
```bash
# Generate API docs
sphinx-apidoc -f -o docs/source/api src/

# Build HTML documentation
sphinx-build -b html docs/source docs/build/html

# Serve documentation locally
cd docs/build/html && python -m http.server 8000

# Open in browser
open http://localhost:8000
```

### Package Building
```bash
# Build distribution packages
uv build

# Verify build
ls dist/
```

### Complete Quality Check Pipeline
```bash
# Run all checks (CI simulation)
flake8 src/ tests/ && \
mypy src/ && \
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80 && \
uv build
```

## 12. Troubleshooting

### Issue 1: mypy Errors on Third-Party Packages

**Problem**: `error: Library stubs not installed for "requests"`

**Solution**:
```bash
# Install type stubs
uv add --dev types-requests

# For other packages, search for types-<package>
uv add --dev types-PyYAML types-redis
```

**Alternative**: Add to `pyproject.toml`:
```toml
[tool.mypy]
ignore_missing_imports = true  # Not recommended, use as last resort
```

### Issue 2: flake8 and Black Conflicts

**Problem**: flake8 complains about formatting that Black enforces

**Solution**: Configure `.flake8` to ignore conflicting rules:
```ini
[flake8]
max-line-length = 100
ignore = E203, E266, W503
extend-ignore = E203, W503
```

### Issue 3: Sphinx Module Discovery Issues

**Problem**: `WARNING: autodoc: failed to import module 'mymodule'`

**Solution**: Ensure correct Python path in `conf.py`:
```python
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))
```

**Alternative**: Install package in editable mode:
```bash
uv pip install -e .
```

### Issue 4: pytest Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution 1**: Add `src` to Python path in `conftest.py`:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

**Solution 2**: Install package in editable mode:
```bash
uv pip install -e .
```

### Issue 5: Coverage Not Detecting All Files

**Problem**: Coverage report shows lower coverage than expected

**Solution**: Configure source paths in `pyproject.toml`:
```toml
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*"]
```

### Issue 6: uv Lock File Conflicts

**Problem**: Merge conflicts in `uv.lock`

**Solution**:
```bash
# Accept one side of the conflict
git checkout --theirs uv.lock  # or --ours

# Regenerate lock file
uv lock

# Commit regenerated file
git add uv.lock
git commit -m "Regenerate uv.lock after merge"
```

### Issue 7: GitHub Actions Workflow Fails

**Problem**: CI pipeline fails on GitHub Actions

**Debugging Steps**:
1. Check workflow logs in GitHub Actions tab
2. Run same commands locally:
   ```bash
   uv sync --dev
   uv run flake8 src/ tests/
   uv run mypy src/
   uv run pytest tests/
   ```
3. Verify Python version matches CI (check workflow YAML)
4. Ensure all dev dependencies are in `pyproject.toml`

### Issue 8: Documentation Build Warnings

**Problem**: Sphinx builds with warnings about missing references

**Solution**: Enable intersphinx mapping in `conf.py`:
```python
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
}
```

---

## Summary

This skill guide provides a complete, production-ready setup for Python backend development with:

✅ **Modern Tooling**: uv, flake8, mypy, pytest, Sphinx  
✅ **CI/CD Ready**: Complete GitHub Actions workflows  
✅ **Type Safety**: Strict mypy configuration with comprehensive examples  
✅ **Documentation**: Sphinx with auto-generated API docs and GitHub Pages deployment  
✅ **Testing**: pytest with >80% coverage target and parametrized tests  
✅ **Best Practices**: PEP 8, PEP 257, PEP 484 compliance  

Follow this guide to build maintainable, well-tested, and well-documented Python backend applications that align with industry standards and the hexagonal architecture principles of the db-explorer project.
