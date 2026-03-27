from dataclasses import dataclass
from enum import Enum
from typing import Any


class UniversalDataType(str, Enum):
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP"
    BINARY = "BINARY"
    UNKNOWN = "UNKNOWN"


@dataclass
class UniversalCell:
    column: str
    type: UniversalDataType
    value: Any


UniversalRow = list[UniversalCell]
