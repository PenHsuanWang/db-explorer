import { useState, useEffect, useRef } from 'react'
import type { JobProgress } from '../types/job'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

interface JobStreamState {
  status: string | null
  progress: JobProgress | null
  error: string | null
  isConnected: boolean
}

export function useJobStream(jobId: string | null): JobStreamState {
  const [state, setState] = useState<JobStreamState>({
    status: null,
    progress: null,
    error: null,
    isConnected: false,
  })
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!jobId) return

    const url = `${API_BASE}/jobs/${jobId}/stream`
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => {
      setState((prev) => ({ ...prev, isConnected: true }))
    }

    es.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data) as JobProgress
      setState((prev) => ({ ...prev, status: 'PROGRESS', progress: data }))
    })

    es.addEventListener('started', (event) => {
      const data = JSON.parse(event.data) as JobProgress
      setState((prev) => ({ ...prev, status: 'STARTED', progress: data }))
    })

    es.addEventListener('complete', (event) => {
      const data = JSON.parse(event.data) as { status: string }
      setState((prev) => ({
        ...prev,
        status: data.status,
        progress: prev.progress ? { ...prev.progress, percent: 100 } : null,
        isConnected: false,
      }))
      es.close()
    })

    es.onerror = () => {
      setState((prev) => ({ ...prev, isConnected: false, error: 'Connection lost' }))
      es.close()
    }

    return () => {
      es.close()
      eventSourceRef.current = null
    }
  }, [jobId])

  return state
}
