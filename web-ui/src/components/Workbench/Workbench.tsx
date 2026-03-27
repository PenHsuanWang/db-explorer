import { useEffect } from 'react'
import type { CleaningConfig } from '../../types/api'
import type { PinnedTable } from '../../types/workbench'
import { useWorkbench } from '../../hooks/useWorkbench'
import { CleaningToolbar } from '../CleaningToolbar'
import { formatValue, isNullValue } from '../../utils/formatValue'
import styles from './Workbench.module.css'

interface WorkbenchProps {
  pinnedTables: PinnedTable[]
  cleaningConfig: CleaningConfig
  onCleaningConfigChange: (config: CleaningConfig) => void
  onRemovePane: (id: string) => void
  onGoHome: () => void
}

export function Workbench({
  pinnedTables,
  cleaningConfig,
  onCleaningConfigChange,
  onRemovePane,
  onGoHome,
}: WorkbenchProps) {
  const { data, loading, error, loadWorkbench } = useWorkbench()

  useEffect(() => {
    loadWorkbench(pinnedTables, cleaningConfig)
  }, [loadWorkbench, pinnedTables, cleaningConfig])

  return (
    <div className={styles.container}>
      <div className={styles.topBar}>
        <button className={styles.homeButton} onClick={onGoHome}>
          ← Home
        </button>
        <h2 className={styles.title}>Workbench</h2>
      </div>

      <CleaningToolbar config={cleaningConfig} onChange={onCleaningConfigChange} />

      <div className={styles.panes}>
        {pinnedTables.length === 0 && (
          <div className={styles.empty}>
            <p>No tables pinned yet.</p>
            <button className={styles.goSearch} onClick={onGoHome}>
              ← Search for tables
            </button>
          </div>
        )}

        {loading && <div className={styles.loading}>Loading workbench data...</div>}
        {error && <div className={styles.error}>Error: {error}</div>}

        {!loading &&
          !error &&
          pinnedTables.map((table) => {
            const paneData = data?.panes[table.id]
            return (
              <div key={table.id} className={styles.pane}>
                <div className={styles.paneHeader}>
                  <div className={styles.paneInfo}>
                    <span className={styles.paneDb}>{table.connection_name}</span>
                    <span className={styles.paneSep}>›</span>
                    <span className={styles.paneTable}>{table.table_name}</span>
                  </div>
                  <button
                    className={styles.closePane}
                    onClick={() => onRemovePane(table.id)}
                    aria-label={`Remove ${table.table_name}`}
                  >
                    ✕
                  </button>
                </div>

                {paneData ? (
                  <div className={styles.tableWrapper}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          {paneData.columns.map((col) => (
                            <th key={col.name} className={styles.th}>
                              {col.name}
                              <span className={styles.colType}>{col.type}</span>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {paneData.rows.map((row, ri) => (
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
                ) : (
                  <div className={styles.paneLoading}>Loading...</div>
                )}
              </div>
            )
          })}
      </div>
    </div>
  )
}
