import { useState } from 'react'
import styles from './GlobalSearch.module.css'

const SUGGESTED_SEARCHES = ['user_id', 'revenue_q3', 'error_logs', 'profit', 'transaction_id']

interface GlobalSearchProps {
  onSearch: (query: string, deepSearch: boolean) => void
  loading?: boolean
}

export function GlobalSearch({ onSearch, loading = false }: GlobalSearchProps) {
  const [query, setQuery] = useState('')
  const [deepSearch, setDeepSearch] = useState(false)
  const [showDeepWarning, setShowDeepWarning] = useState(false)

  const handleSubmit = () => {
    if (query.trim()) {
      onSearch(query.trim(), deepSearch)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSubmit()
  }

  return (
    <div className={styles.container}>
      <div className={styles.hero}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>🗄️</span>
          <h1 className={styles.logoText}>DB Explorer</h1>
        </div>
        <p className={styles.tagline}>One Search, All Data.</p>

        <div className={styles.searchWrapper}>
          <div className={styles.searchBox}>
            <span className={styles.searchIcon}>🔍</span>
            <input
              className={styles.input}
              type="text"
              placeholder="Search tables, columns, schemas..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
            />
            <button
              className={styles.searchButton}
              onClick={handleSubmit}
              disabled={loading || !query.trim()}
            >
              {loading ? '...' : 'Search'}
            </button>
          </div>

          <div className={styles.deepSearchRow}>
            <label className={styles.deepSearchLabel}>
              <input
                type="checkbox"
                checked={deepSearch}
                onChange={(e) => {
                  setDeepSearch(e.target.checked)
                  setShowDeepWarning(e.target.checked)
                }}
              />
              <span>Deep Search</span>
            </label>
            {showDeepWarning && (
              <span className={styles.warning}>
                ⚠️ This may take longer as it scans actual data values
              </span>
            )}
          </div>
        </div>

        <div className={styles.chips}>
          <span className={styles.chipsLabel}>Suggested:</span>
          {SUGGESTED_SEARCHES.map((s) => (
            <button
              key={s}
              className={styles.chip}
              onClick={() => {
                setQuery(s)
                onSearch(s, deepSearch)
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
