import { useState, useCallback, useRef } from 'react'
import type { SearchResult } from '../types/api'
import { search } from '../services/searchService'

const MAX_CACHE = 20

export function useSearch() {
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const cacheRef = useRef<Map<string, SearchResult[]>>(new Map())
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const activeRef = useRef(0)

  const runSearch = useCallback(async (query: string, deepSearch = false) => {
    if (!query.trim()) return

    // Cancel any pending debounce
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }

    const cacheKey = `${query}::${deepSearch}`
    const cached = cacheRef.current.get(cacheKey)
    if (cached) {
      setResults(cached)
      return
    }

    setLoading(true)
    setError(null)

    const searchId = ++activeRef.current

    await new Promise<void>((resolve) => {
      timerRef.current = setTimeout(resolve, 300)
    })

    // Abort if a newer search was triggered during debounce
    if (activeRef.current !== searchId) return

    try {
      const data = await search({ query, deep_search: deepSearch })

      // Only update state if this is still the latest search
      if (activeRef.current !== searchId) return

      setResults(data.results)

      // Update cache with LRU eviction
      const cache = cacheRef.current
      if (cache.size >= MAX_CACHE) {
        const firstKey = cache.keys().next().value
        if (firstKey !== undefined) cache.delete(firstKey)
      }
      cache.set(cacheKey, data.results)
    } catch (err: unknown) {
      if (activeRef.current === searchId) {
        setError(err instanceof Error ? err.message : 'Search failed')
      }
    } finally {
      if (activeRef.current === searchId) {
        setLoading(false)
      }
    }
  }, [])

  return { results, loading, error, runSearch }
}
