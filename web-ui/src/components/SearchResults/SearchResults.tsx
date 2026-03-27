import type { SearchResult } from '../../types/api'
import type { PinnedTable } from '../../types/workbench'
import { DataCard } from '../DataCard'
import { Dock } from '../Dock'
import styles from './SearchResults.module.css'

interface SearchResultsProps {
  query: string
  results: SearchResult[]
  loading: boolean
  pinnedTables: PinnedTable[]
  onBack: () => void
  onPeek: (result: SearchResult) => void
  onPin: (table: PinnedTable) => void
  onUnpin: (id: string) => void
  onOpenWorkbench: () => void
}

export function SearchResults({
  query,
  results,
  loading,
  pinnedTables,
  onBack,
  onPeek,
  onPin,
  onUnpin,
  onOpenWorkbench,
}: SearchResultsProps) {
  const pinnedIds = new Set(pinnedTables.map((t) => t.id))

  const sources = [...new Set(results.map((r) => r.source_db))]
  const matchTypes = [...new Set(results.map((r) => r.match_type))]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button className={styles.backButton} onClick={onBack}>
          ← Back
        </button>
        <div className={styles.queryInfo}>
          <span className={styles.queryLabel}>Search:</span>
          <span className={styles.query}>&quot;{query}&quot;</span>
          {!loading && (
            <span className={styles.count}>({results.length} results)</span>
          )}
        </div>
      </div>

      <div className={styles.body}>
        <aside className={styles.sidebar}>
          <div className={styles.facetGroup}>
            <h3 className={styles.facetTitle}>SOURCE</h3>
            {sources.map((src) => (
              <label key={src} className={styles.facetItem} aria-hidden="true">
                <input type="checkbox" defaultChecked readOnly tabIndex={-1} />
                <span>{src}</span>
              </label>
            ))}
          </div>
          <div className={styles.facetGroup}>
            <h3 className={styles.facetTitle}>MATCH TYPE</h3>
            {matchTypes.map((mt) => (
              <label key={mt} className={styles.facetItem} aria-hidden="true">
                <input type="checkbox" defaultChecked readOnly tabIndex={-1} />
                <span>{mt}</span>
              </label>
            ))}
          </div>
        </aside>

        <main className={styles.main}>
          {loading && <div className={styles.loading}>Searching...</div>}
          {!loading && results.length === 0 && (
            <div className={styles.empty}>No results found for &quot;{query}&quot;</div>
          )}
          {!loading && results.length > 0 && (
            <div className={styles.grid}>
              {results.map((result) => (
                <DataCard
                  key={result.id}
                  result={result}
                  isPinned={pinnedIds.has(result.id)}
                  onPeek={onPeek}
                  onPin={onPin}
                  onUnpin={onUnpin}
                />
              ))}
            </div>
          )}
        </main>
      </div>

      <Dock
        pinnedTables={pinnedTables}
        onUnpin={onUnpin}
        onOpenWorkbench={onOpenWorkbench}
      />
    </div>
  )
}
