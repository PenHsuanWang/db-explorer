import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Job } from '../types/job'
import * as jobService from '../services/jobService'
import styles from './JobsPage.module.css'

const ACTIVE_STATUSES = new Set(['PENDING', 'STARTED', 'PROGRESS'])

function badgeClass(status: string): string {
  switch (status) {
    case 'PENDING':
      return styles.badgePending
    case 'STARTED':
      return styles.badgeStarted
    case 'PROGRESS':
      return styles.badgeProgress
    case 'SUCCESS':
      return styles.badgeSuccess
    case 'FAILURE':
      return styles.badgeFailure
    default:
      return styles.badgePending
  }
}

export function JobsPage() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchJobs = useCallback(async () => {
    try {
      const data = await jobService.listJobs()
      setJobs(data)
      setError(null)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  // Poll for updates when there are active jobs
  useEffect(() => {
    const hasActive = jobs.some((j) => ACTIVE_STATUSES.has(j.status))
    if (!hasActive) return

    const interval = setInterval(fetchJobs, 5000)
    return () => clearInterval(interval)
  }, [jobs, fetchJobs])

  const handleDelete = async (id: string) => {
    await jobService.deleteJob(id)
    setJobs((prev) => prev.filter((j) => j.id !== id))
  }

  const canDelete = (status: string) => status === 'SUCCESS' || status === 'FAILURE'

  return (
    <div className={styles.page}>
      <div className={styles.topBar}>
        <button className={styles.homeButton} onClick={() => navigate('/')}>
          ← Home
        </button>
        <h2 className={styles.title}>Jobs</h2>
      </div>

      <div className={styles.content}>
        {loading && <div className={styles.loading}>Loading jobs...</div>}
        {error && <div className={styles.error}>Error: {error}</div>}

        {!loading && !error && jobs.length === 0 && (
          <div className={styles.empty}>No jobs yet.</div>
        )}

        {!loading && !error && jobs.length > 0 && (
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>Type</th>
                <th className={styles.th}>Status</th>
                <th className={styles.th}>Progress</th>
                <th className={styles.th}>Created</th>
                <th className={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => {
                const percent = job.progress_meta?.percent ?? 0
                return (
                  <tr key={job.id} className={styles.tr}>
                    <td className={styles.td}>{job.job_type}</td>
                    <td className={styles.td}>
                      <span className={`${styles.badge} ${badgeClass(job.status)}`}>
                        {job.status}
                      </span>
                    </td>
                    <td className={styles.td}>
                      <div className={styles.progressCell}>
                        <div className={styles.progressTrack}>
                          <div
                            className={styles.progressFill}
                            style={{ width: `${Math.min(percent, 100)}%` }}
                          />
                        </div>
                        <span className={styles.progressText}>{Math.round(percent)}%</span>
                      </div>
                    </td>
                    <td className={styles.td}>
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                    <td className={styles.td}>
                      {canDelete(job.status) && (
                        <button
                          className={styles.deleteButton}
                          onClick={() => handleDelete(job.id)}
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
