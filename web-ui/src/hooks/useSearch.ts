import { useState, useCallback } from 'react'
import type { SearchResult } from '../types/api'
import { search } from '../services/searchService'

export function useSearch() {
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runSearch = useCallback(async (query: string, deepSearch = false) => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    try {
      const data = await search({ query, deep_search: deepSearch })
      setResults(data.results)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }, [])

  return { results, loading, error, runSearch }
}
