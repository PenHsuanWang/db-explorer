import type { SearchResult } from '../../types/api'
import type { PinnedTable } from '../../types/workbench'
import { getTypeColor } from '../../utils/typeColors'
import styles from './DataCard.module.css'

const DB_ICONS: Record<string, string> = {
  oracle: '🔶',
  clickhouse: '🔵',
  databricks: '💠',
  mock: '🟢',
}

interface DataCardProps {
  result: SearchResult
  isPinned: boolean
  onPeek: (result: SearchResult) => void
  onPin: (table: PinnedTable) => void
  onUnpin: (id: string) => void
}

export function DataCard({ result, isPinned, onPeek, onPin, onUnpin }: DataCardProps) {
  const icon = DB_ICONS[result.db_type] ?? '⚪'

  const handlePin = () => {
    if (isPinned) {
      onUnpin(result.id)
    } else {
      onPin({
        id: result.id,
        connection_id: result.source_db,
        connection_name: result.source_db,
        db_type: result.db_type,
        schema_name: result.schema_name,
        table_name: result.table_name,
        source_result: result,
      })
    }
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.icon}>{icon}</span>
        <span className={styles.dbType}>{result.db_type.toUpperCase()}</span>
        <span className={styles.tableName}>{result.table_name}</span>
      </div>

      <div className={styles.breadcrumb}>
        {result.source_db} &rsaquo; {result.schema_name} &rsaquo; {result.table_name}
      </div>

      <div className={styles.matchSnippet}>
        <span className={styles.matchType}>{result.match_type}:</span> {result.match_snippet}
      </div>

      {result.preview_columns.length > 0 && (
        <div className={styles.preview}>
          {result.preview_columns.slice(0, 3).map((col) => (
            <span
              key={col.name}
              className={styles.colBadge}
              style={{ borderColor: getTypeColor(col.type) }}
            >
              {col.name}{' '}
              <span className={styles.colType} style={{ color: getTypeColor(col.type) }}>
                {col.type}
              </span>
            </span>
          ))}
        </div>
      )}

      <div className={styles.actions}>
        <button className={styles.peekButton} onClick={() => onPeek(result)}>
          👁 Peek
        </button>
        <button
          className={isPinned ? styles.pinnedButton : styles.pinButton}
          onClick={handlePin}
        >
          {isPinned ? '✓ Pinned' : 'Pin +'}
        </button>
      </div>
    </div>
  )
}
