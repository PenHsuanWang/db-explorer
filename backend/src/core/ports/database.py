import re
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, Optional

from src.core.domain.types import UniversalDataType


class ConnectorError(Exception):
    """Base error for connector failures."""


class TransientError(ConnectorError):
    """Transient / retryable error (e.g. network timeout)."""


class ReadOnlyViolationError(ConnectorError):
    """Raised when a write or DDL statement is attempted."""


class ConfigurationError(ConnectorError):
    """Raised when the connector is misconfigured."""


# Regex for safe SQL identifiers: letters, digits, underscores, dollar signs.
# Rejects anything that could be used to inject SQL (spaces, quotes, semicolons, etc.).
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def sanitize_identifier(name: str) -> str:
    """Validate and return a safe SQL identifier.

    Raises ConfigurationError if the identifier contains unsafe characters.
    """
    if not _SAFE_IDENTIFIER_RE.match(name):
        raise ConfigurationError(
            f"Unsafe SQL identifier '{name}'. "
            "Identifiers must contain only letters, digits, underscores, or dollar signs."
        )
    return name


_WRITE_KEYWORDS = frozenset(
    [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "REPLACE",
        "MERGE",
        "UPSERT",
        "CALL",
        "EXEC",
        "EXECUTE",
        "GRANT",
        "REVOKE",
    ]
)


class DatabasePort(ABC):
    """Abstract read-only database adapter (port)."""

    @abstractmethod
    def connect(self) -> None:
        """Establish a read-only connection."""

    @abstractmethod
    def close(self) -> None:
        """Release all resources."""

    @abstractmethod
    def execute_safe_read(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
        max_rows: int = 1000,
    ) -> list[dict[str, Any]]:
        """Execute a read-only SQL statement and return at most max_rows rows."""

    @abstractmethod
    def execute_query_stream(
        self,
        sql: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Iterator[dict[str, Any]]:
        """Stream rows from a read-only SQL statement."""

    @abstractmethod
    def fetch_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> dict[str, UniversalDataType]:
        """Return column-name → UniversalDataType mapping for a table."""

    @abstractmethod
    def fetch_tables(self, schema: Optional[str] = None) -> list[dict[str, Any]]:
        """Return list of table metadata dicts."""

    def _validate_read_only(self, sql: str) -> None:
        """Raise ReadOnlyViolationError if sql contains write/DDL keywords."""
        first_word = sql.strip().split()[0].upper() if sql.strip() else ""
        if first_word in _WRITE_KEYWORDS:
            raise ReadOnlyViolationError(
                f"Write/DDL operation '{first_word}' is not permitted in read-only mode."
            )
        # Secondary check: scan entire statement for dangerous keywords at word boundaries
        upper_sql = sql.upper()
        for kw in _WRITE_KEYWORDS:
            pattern = rf"\b{kw}\b"
            if re.search(pattern, upper_sql):
                raise ReadOnlyViolationError(
                    f"Write/DDL keyword '{kw}' detected in SQL statement."
                )
