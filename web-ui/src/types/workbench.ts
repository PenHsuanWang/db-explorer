import type { DbType, SearchResult } from './api'

export interface PinnedTable {
  id: string
  connection_id: string
  connection_name: string
  db_type: DbType
  schema_name: string
  table_name: string
  source_result: SearchResult
}
