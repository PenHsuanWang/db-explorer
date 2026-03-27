import { useState, useCallback } from 'react'
import type { WorkbenchResponse, CleaningConfig } from '../types/api'
import type { PinnedTable } from '../types/workbench'
import { fetchWorkbench } from '../services/workbenchService'

export function useWorkbench() {
  const [data, setData] = useState<WorkbenchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadWorkbench = useCallback(
    async (pinnedTables: PinnedTable[], cleaningConfig?: CleaningConfig) => {
      if (pinnedTables.length === 0) {
        setData(null)
        return
      }
      setLoading(true)
      setError(null)
      try {
        const result = await fetchWorkbench({
          panes: pinnedTables.map((t) => ({
            connection_id: t.connection_id,
            table_name: t.table_name,
            schema_name: t.schema_name,
            pane_id: t.id,
          })),
          cleaning_config: cleaningConfig,
        })
        setData(result)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Workbench load failed')
      } finally {
        setLoading(false)
      }
    },
    []
  )

  return { data, loading, error, loadWorkbench }
}
