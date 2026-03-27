from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from src.core.domain.models import CleaningConfig
from src.core.domain.types import UniversalCell, UniversalDataType, UniversalRow

logger = logging.getLogger(__name__)

_NULL_LIKE = frozenset(["", "null", "none", "na", "n/a", "nan", "-"])


def _unify_null(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float):
        import math

        if math.isnan(value):
            return None
    if isinstance(value, str) and value.strip().lower() in _NULL_LIKE:
        return None
    return value


def _cast_value(value: Any, target_type: UniversalDataType) -> Any:  # noqa: PLR0911
    if value is None:
        return None
    try:
        if target_type == UniversalDataType.TEXT:
            return str(value)
        if target_type == UniversalDataType.INTEGER:
            return int(float(str(value)))
        if target_type == UniversalDataType.FLOAT:
            return float(str(value))
        if target_type == UniversalDataType.BOOLEAN:
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in ("true", "1", "yes")
        if target_type == UniversalDataType.TIMESTAMP:
            if isinstance(value, datetime):
                return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
            parsed = datetime.fromisoformat(str(value))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
        if target_type == UniversalDataType.BINARY:
            if isinstance(value, (bytes, bytearray)):
                return value
            return str(value).encode()
    except (ValueError, TypeError, AttributeError):
        logger.debug("Failed to cast %r to %s", value, target_type)
    return value


def _row_fingerprint(row: dict[str, Any]) -> str:
    serialized = str(sorted(row.items()))
    return hashlib.sha256(serialized.encode()).hexdigest()


class CleaningEngine:
    """Transforms raw database rows into UniversalRow lists in memory."""

    def apply(
        self,
        raw_rows: list[dict[str, Any]],
        schema: dict[str, UniversalDataType],
        config: CleaningConfig,
    ) -> list[UniversalRow]:
        normalized = self._normalize(raw_rows, config)
        deduplicated = self._deduplicate(normalized)
        return self._build_universal_rows(deduplicated, schema, config)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalize(
        self, rows: list[dict[str, Any]], config: CleaningConfig
    ) -> list[dict[str, Any]]:
        result = []
        for row in rows:
            new_row: dict[str, Any] = {}
            for col, val in row.items():
                val = _unify_null(val)
                if val is not None and config.trim_strings and isinstance(val, str):
                    val = val.strip()
                # Apply column alias
                col_name = config.column_aliases.get(col, col)
                new_row[col_name] = val
            result.append(new_row)
        return result

    def _deduplicate(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for row in rows:
            fp = _row_fingerprint(row)
            if fp not in seen:
                seen.add(fp)
                unique.append(row)
        return unique

    def _build_universal_rows(
        self,
        rows: list[dict[str, Any]],
        schema: dict[str, UniversalDataType],
        config: CleaningConfig,
    ) -> list[UniversalRow]:
        universal: list[UniversalRow] = []
        for row in rows:
            cells: UniversalRow = []
            for col, val in row.items():
                # Resolve type: override > schema > UNKNOWN
                type_key = config.type_overrides.get(col)
                if type_key:
                    try:
                        dtype = UniversalDataType(type_key.upper())
                    except ValueError:
                        dtype = schema.get(col, UniversalDataType.UNKNOWN)
                else:
                    dtype = schema.get(col, UniversalDataType.UNKNOWN)

                casted_val = _cast_value(val, dtype)

                if config.hide_null_values and casted_val is None:
                    continue

                # Format timestamps
                if dtype == UniversalDataType.TIMESTAMP and isinstance(casted_val, datetime):
                    casted_val = casted_val.isoformat()

                cells.append(UniversalCell(column=col, type=dtype, value=casted_val))
            universal.append(cells)
        return universal
