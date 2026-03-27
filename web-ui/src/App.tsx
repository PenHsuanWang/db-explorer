import { useState, useCallback } from 'react'
import { Routes, Route } from 'react-router-dom'
import type { SearchResult, CleaningConfig } from './types/api'
import type { PinnedTable } from './types/workbench'
import { useSearch } from './hooks/useSearch'
import { GlobalSearch } from './components/GlobalSearch'
import { SearchResults } from './components/SearchResults'
import { PeekModal } from './components/PeekModal'
import { Workbench } from './components/Workbench'
import { ConnectionStatus } from './components/ConnectionStatus'
import { ProtectedRoute } from './components/ProtectedRoute'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ToastContainer } from './components/Toast'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { JobsPage } from './pages/JobsPage'
import { AuthProvider } from './contexts/AuthContext'
import { ConnectionProvider } from './contexts/ConnectionContext'
import styles from './App.module.css'

type View = 'search' | 'results' | 'workbench'

const DEFAULT_CLEANING_CONFIG: CleaningConfig = {
  hide_null_values: false,
  date_format: 'ISO8601',
  trim_strings: true,
}

function MainView() {
  const [view, setView] = useState<View>('search')
  const [searchQuery, setSearchQuery] = useState('')
  const [pinnedTables, setPinnedTables] = useState<PinnedTable[]>([])
  const [cleaningConfig, setCleaningConfig] = useState<CleaningConfig>(DEFAULT_CLEANING_CONFIG)
  const [peekTarget, setPeekTarget] = useState<SearchResult | null>(null)

  const { results, loading: searchLoading, runSearch } = useSearch()

  const handleSearch = useCallback(
    (query: string, deepSearch: boolean) => {
      setSearchQuery(query)
      setView('results')
      runSearch(query, deepSearch)
    },
    [runSearch]
  )

  const handlePin = useCallback((table: PinnedTable) => {
    setPinnedTables((prev) => {
      if (prev.some((t) => t.id === table.id)) return prev
      return [...prev, table]
    })
  }, [])

  const handleUnpin = useCallback((id: string) => {
    setPinnedTables((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const handleOpenWorkbench = useCallback(() => {
    setView('workbench')
  }, [])

  const handleRemovePane = useCallback((id: string) => {
    setPinnedTables((prev) => {
      const next = prev.filter((t) => t.id !== id)
      if (next.length === 0) setView('search')
      return next
    })
  }, [])

  const pinnedIds = new Set(pinnedTables.map((t) => t.id))

  return (
    <div className={styles.app}>
      {view === 'search' && (
        <GlobalSearch onSearch={handleSearch} loading={searchLoading} />
      )}

      {view === 'results' && (
        <SearchResults
          query={searchQuery}
          results={results}
          loading={searchLoading}
          pinnedTables={pinnedTables}
          onBack={() => setView('search')}
          onPeek={setPeekTarget}
          onPin={handlePin}
          onUnpin={handleUnpin}
          onOpenWorkbench={handleOpenWorkbench}
        />
      )}

      {view === 'workbench' && (
        <Workbench
          pinnedTables={pinnedTables}
          cleaningConfig={cleaningConfig}
          onCleaningConfigChange={setCleaningConfig}
          onRemovePane={handleRemovePane}
          onGoHome={() => setView('search')}
        />
      )}

      {peekTarget && (
        <PeekModal
          result={peekTarget}
          isPinned={pinnedIds.has(peekTarget.id)}
          onPin={handlePin}
          onClose={() => setPeekTarget(null)}
        />
      )}

      {view !== 'workbench' && <ConnectionStatus />}
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ConnectionProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/jobs" element={<JobsPage />} />
              <Route path="/*" element={<MainView />} />
            </Route>
          </Routes>
          <ToastContainer />
        </ConnectionProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}
