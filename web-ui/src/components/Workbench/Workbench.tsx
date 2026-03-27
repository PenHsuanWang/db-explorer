import { useEffect, useState, useCallback } from 'react'
import type { CleaningConfig } from '../../types/api'
import type { PinnedTable } from '../../types/workbench'
import { useWorkbench } from '../../hooks/useWorkbench'
import { CleaningToolbar } from '../CleaningToolbar'
import { formatValue, isNullValue } from '../../utils/formatValue'
import * as savedWorkbenchService from '../../services/savedWorkbenchService'
import type { SavedWorkbench } from '../../services/savedWorkbenchService'
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
  const [showSaveInput, setShowSaveInput] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [saving, setSaving] = useState(false)
  const [savedList, setSavedList] = useState<SavedWorkbench[]>([])
  const [showLoadMenu, setShowLoadMenu] = useState(false)

  useEffect(() => {
    loadWorkbench(pinnedTables, cleaningConfig)
  }, [loadWorkbench, pinnedTables, cleaningConfig])

  const handleSave = useCallback(async () => {
    if (!saveName.trim()) return
    setSaving(true)
    try {
      await savedWorkbenchService.createSavedWorkbench({
        name: saveName.trim(),
        panes_config: { pinnedTables },
        cleaning_cfg: cleaningConfig as Record<string, unknown>,
      })
      setSaveName('')
      setShowSaveInput(false)
    } finally {
      setSaving(false)
    }
  }, [saveName, pinnedTables, cleaningConfig])

  const handleLoadToggle = useCallback(async () => {
    if (showLoadMenu) {
      setShowLoadMenu(false)
      return
    }
    const list = await savedWorkbenchService.listSavedWorkbenches()
    setSavedList(list)
    setShowLoadMenu(true)
  }, [showLoadMenu])

  const handleLoadSelect = useCallback(
    async (id: string) => {
      const wb = await savedWorkbenchService.getSavedWorkbench(id)
      if (wb.cleaning_cfg) {
        onCleaningConfigChange(wb.cleaning_cfg as CleaningConfig)
      }
      setShowLoadMenu(false)
    },
    [onCleaningConfigChange]
  )

  return (
    <div className={styles.container}>
      <div className={styles.topBar}>
        <button className={styles.homeButton} onClick={onGoHome}>
          ← Home
        </button>
        <h2 className={styles.title}>Workbench</h2>

        <div className={styles.toolbarActions}>
          {showSaveInput ? (
            <div className={styles.saveInputGroup}>
              <input
                className={styles.saveInput}
                type="text"
                placeholder="Workbench name"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSave()}
              />
              <button className={styles.saveConfirm} onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save'}
              </button>
              <button className={styles.saveCancel} onClick={() => setShowSaveInput(false)}>
                Cancel
              </button>
            </div>
          ) : (
            <button className={styles.actionButton} onClick={() => setShowSaveInput(true)}>
              💾 Save Workbench
            </button>
          )}

          <div className={styles.loadWrapper}>
            <button className={styles.actionButton} onClick={handleLoadToggle}>
              📂 Load Workbench
            </button>
            {showLoadMenu && (
              <div className={styles.loadMenu}>
                {savedList.length === 0 ? (
                  <div className={styles.loadEmpty}>No saved workbenches</div>
                ) : (
                  savedList.map((wb) => (
                    <button
                      key={wb.id}
                      className={styles.loadItem}
                      onClick={() => handleLoadSelect(wb.id)}
                    >
                      {wb.name}
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
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
