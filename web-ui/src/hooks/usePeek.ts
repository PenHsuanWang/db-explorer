import { useState, useCallback } from 'react'
import type { PeekResponse } from '../types/api'
import { peek } from '../services/peekService'

export function usePeek() {
  const [data, setData] = useState<PeekResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPeek = useCallback(
    async (connectionId: string, tableName: string, schemaName?: string) => {
      setLoading(true)
      setError(null)
      try {
        const result = await peek({
          connection_id: connectionId,
          table_name: tableName,
          schema_name: schemaName,
        })
        setData(result)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Peek failed')
      } finally {
        setLoading(false)
      }
    },
    []
  )

  const reset = useCallback(() => {
    setData(null)
    setError(null)
  }, [])

  return { data, loading, error, fetchPeek, reset }
}
