import { useEffect } from 'react'
import type { SearchResult } from '../../types/api'
import type { PinnedTable } from '../../types/workbench'
import { usePeek } from '../../hooks/usePeek'
import { formatValue, isNullValue } from '../../utils/formatValue'
import styles from './PeekModal.module.css'

interface PeekModalProps {
  result: SearchResult
  isPinned: boolean
  onPin: (table: PinnedTable) => void
  onClose: () => void
}

export function PeekModal({ result, isPinned, onPin, onClose }: PeekModalProps) {
  const { data, loading, error, fetchPeek } = usePeek()

  useEffect(() => {
    fetchPeek(result.source_db, result.table_name, result.schema_name)
  }, [fetchPeek, result.source_db, result.table_name, result.schema_name])

  const handlePin = () => {
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

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>
            Preview: {result.source_db} &rsaquo; {result.schema_name} &rsaquo; {result.table_name}
          </h2>
          <button className={styles.closeButton} onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className={styles.body}>
          {loading && <div className={styles.loading}>Loading sample data...</div>}
          {error && <div className={styles.error}>Error: {error}</div>}
          {data && (
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    {data.columns.map((col) => (
                      <th key={col.name} className={styles.th}>
                        {col.name}
                        <span className={styles.colType}>{col.type}</span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((row, ri) => (
                    <tr key={ri} className={styles.tr}>
                      {row.map((cell, ci) => (
                        <td key={ci} className={styles.td}>
                          {isNullValue(cell.value) ? (
                            <span className={styles.nullValue}>&lt;NULL&gt;</span>
                          ) : (
                            formatValue(cell.value)
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className={styles.footer}>
          <button
            className={isPinned ? styles.pinnedButton : styles.pinButton}
            onClick={handlePin}
            disabled={isPinned}
          >
            {isPinned ? '✓ Pinned to Workbench' : 'Pin to Workbench'}
          </button>
        </div>
      </div>
    </div>
  )
}
