export type DbType = 'oracle' | 'clickhouse' | 'databricks' | 'mock'

export interface Connection {
  id: string
  name: string
  db_type: DbType
  host: string
  port: number
  database: string
  status: 'connected' | 'disconnected' | 'error'
}

export interface ConnectionsResponse {
  connections: Connection[]
}

export interface CleaningConfig {
  hide_null_values?: boolean
  date_format?: string
  trim_strings?: boolean
  column_aliases?: Record<string, string>
  type_overrides?: Record<string, string>
}

export interface PreviewColumn {
  name: string
  type: string
}

export interface SearchResult {
  id: string
  source_db: string
  db_type: DbType
  schema_name: string
  table_name: string
  column_name?: string
  match_type: string
  match_snippet: string
  preview_columns: PreviewColumn[]
}

export interface SearchRequest {
  query: string
  deep_search?: boolean
  source_filter?: string[]
  match_type_filter?: string[]
}

export interface SearchResponse {
  results: SearchResult[]
}

export interface UniversalCell {
  column: string
  type: string
  value: unknown
}

export type UniversalRow = UniversalCell[]

export interface ColumnMeta {
  name: string
  type: string
}

export interface PeekRequest {
  connection_id: string
  table_name: string
  schema_name?: string
  cleaning_config?: CleaningConfig
}

export interface PeekResponse {
  columns: ColumnMeta[]
  rows: UniversalRow[]
}

export interface WorkbenchPaneRequest {
  connection_id: string
  table_name: string
  schema_name?: string
  pane_id: string
}

export interface WorkbenchRequest {
  panes: WorkbenchPaneRequest[]
  cleaning_config?: CleaningConfig
}

export interface WorkbenchPaneData {
  columns: ColumnMeta[]
  rows: UniversalRow[]
}

export interface WorkbenchResponse {
  panes: Record<string, WorkbenchPaneData>
}
