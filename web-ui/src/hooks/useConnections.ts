import { useState, useEffect } from 'react'
import type { Connection } from '../types/api'
import { getConnections } from '../services/connectionService'

export function useConnections() {
  const [connections, setConnections] = useState<Connection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getConnections()
      .then((data) => {
        if (!cancelled) {
          setConnections(data.connections)
          setError(null)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load connections')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { connections, loading, error }
}
