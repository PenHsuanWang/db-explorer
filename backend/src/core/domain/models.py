from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


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


# ---------------------------------------------------------------------------
# Authentication schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int


# ---------------------------------------------------------------------------
# Saved workbench schemas
# ---------------------------------------------------------------------------


class SavedWorkbenchCreate(BaseModel):
    name: str
    panes_config: dict = Field(default_factory=dict)
    cleaning_cfg: dict = Field(default_factory=dict)


class SavedWorkbenchResponse(BaseModel):
    id: str
    name: str
    panes_config: dict
    cleaning_cfg: dict
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Job schemas
# ---------------------------------------------------------------------------


class JobCreate(BaseModel):
    job_type: str
    payload: dict = Field(default_factory=dict)


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    payload: Optional[dict] = None
    progress_meta: Optional[dict] = None
    result_data: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)
