import { useJobStream } from '../../hooks/useJobStream'
import styles from './JobProgressBar.module.css'

interface JobProgressBarProps {
  jobId: string | null
}

function statusClass(status: string | null): string {
  switch (status) {
    case 'PROGRESS':
    case 'STARTED':
      return styles.statusProgress
    case 'SUCCESS':
      return styles.statusSuccess
    case 'FAILURE':
      return styles.statusFailure
    default:
      return styles.statusPending
  }
}

function fillClass(status: string | null): string {
  switch (status) {
    case 'PROGRESS':
    case 'STARTED':
      return styles.fillProgress
    case 'SUCCESS':
      return styles.fillSuccess
    case 'FAILURE':
      return styles.fillFailure
    default:
      return styles.fillProgress
  }
}

export function JobProgressBar({ jobId }: JobProgressBarProps) {
  const { status, progress, error } = useJobStream(jobId)

  if (!jobId) return null

  const percent = progress?.percent ?? 0
  const current = progress?.current ?? 0
  const total = progress?.total ?? 0

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={`${styles.status} ${statusClass(status)}`}>
          {status ?? 'PENDING'}
        </span>
        {total > 0 && (
          <span className={styles.steps}>
            {current}/{total}
          </span>
        )}
      </div>
      <div className={styles.track}>
        <div
          className={`${styles.fill} ${fillClass(status)}`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
      {progress?.message && <p className={styles.message}>{progress.message}</p>}
      {error && <p className={styles.error}>{error}</p>}
    </div>
  )
}
