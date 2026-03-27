from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, SecretStr


class CleaningConfig(BaseModel):
    hide_null_values: bool = False
    date_format: str = "ISO8601"
    trim_strings: bool = True
    column_aliases: dict[str, str] = Field(default_factory=dict)
    type_overrides: dict[str, str] = Field(default_factory=dict)


class SearchResult(BaseModel):
    id: str
    source_db: str
    db_type: str
    schema_name: Optional[str] = None
    table_name: str
    column_name: Optional[str] = None
    match_type: str
    match_snippet: str
    preview_columns: list[dict[str, str]] = Field(default_factory=list)


class ConnectionConfig(BaseModel):
    id: Optional[str] = None
    name: str
    db_type: str
    host: str = ""
    port: Optional[int] = None
    database: str = ""
    username: str = ""
    password: Optional[SecretStr] = None
    extra_params: dict[str, str] = Field(default_factory=dict)


class PeekRequest(BaseModel):
    connection_id: str
    table_name: str
    schema_name: Optional[str] = None
    cleaning_config: CleaningConfig = Field(default_factory=CleaningConfig)


class WorkbenchPane(BaseModel):
    connection_id: str
    table_name: str
    schema_name: Optional[str] = None
    pane_id: str


class WorkbenchRequest(BaseModel):
    panes: list[WorkbenchPane]
    cleaning_config: CleaningConfig = Field(default_factory=CleaningConfig)


class SearchRequest(BaseModel):
    query: str
    deep_search: bool = False
    source_filter: Optional[list[str]] = None
    match_type_filter: Optional[str] = None
