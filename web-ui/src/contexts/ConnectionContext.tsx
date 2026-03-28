import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'
import type { Connection } from '../types/api'
import * as connectionService from '../services/connectionService'

interface ConnectionContextValue {
  connections: Connection[]
  loading: boolean
  error: string | null
  addConnection: (conn: Connection) => Promise<void>
  removeConnection: (id: string) => Promise<void>
  refreshConnections: () => Promise<void>
}

const ConnectionContext = createContext<ConnectionContextValue | null>(null)

export function ConnectionProvider({ children }: { children: ReactNode }) {
  const [connections, setConnections] = useState<Connection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refreshConnections = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await connectionService.getConnections()
      setConnections(data.connections)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load connections')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshConnections()
  }, [refreshConnections])

  const addConnection = useCallback(
    async (conn: Connection) => {
      await connectionService.createConnection(conn)
      await refreshConnections()
    },
    [refreshConnections]
  )

  const removeConnection = useCallback(
    async (id: string) => {
      await connectionService.deleteConnection(id)
      await refreshConnections()
    },
    [refreshConnections]
  )

  return (
    <ConnectionContext.Provider
      value={{ connections, loading, error, addConnection, removeConnection, refreshConnections }}
    >
      {children}
    </ConnectionContext.Provider>
  )
}

export function useConnectionContext(): ConnectionContextValue {
  const ctx = useContext(ConnectionContext)
  if (!ctx) throw new Error('useConnectionContext must be used within ConnectionProvider')
  return ctx
}
