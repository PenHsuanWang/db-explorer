import { useConnections } from '../../hooks/useConnections'
import styles from './ConnectionStatus.module.css'

const DB_ICONS: Record<string, string> = {
  oracle: '🔶',
  clickhouse: '🔵',
  databricks: '💠',
  mock: '🟢',
}

export function ConnectionStatus() {
  const { connections, loading } = useConnections()

  return (
    <div className={styles.bar}>
      <span className={styles.label}>Connections:</span>
      {loading && <span className={styles.loading}>Loading...</span>}
      {connections.map((conn) => (
        <span
          key={conn.id}
          className={`${styles.pill} ${conn.status === 'connected' ? styles.connected : styles.disconnected}`}
        >
          {DB_ICONS[conn.db_type] ?? '⚪'} {conn.name}
        </span>
      ))}
      <button className={styles.addButton}>+ Add Connection</button>
    </div>
  )
}
