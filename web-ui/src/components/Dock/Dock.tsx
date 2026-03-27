import type { PinnedTable } from '../../types/workbench'
import styles from './Dock.module.css'

const DB_ICONS: Record<string, string> = {
  oracle: '🔶',
  clickhouse: '🔵',
  databricks: '💠',
  mock: '🟢',
}

interface DockProps {
  pinnedTables: PinnedTable[]
  onUnpin: (id: string) => void
  onOpenWorkbench: () => void
}

export function Dock({ pinnedTables, onUnpin, onOpenWorkbench }: DockProps) {
  if (pinnedTables.length === 0) return null

  return (
    <div className={styles.dock}>
      <span className={styles.dockLabel}>Pinned ({pinnedTables.length}):</span>
      <div className={styles.chips}>
        {pinnedTables.map((t) => (
          <span key={t.id} className={styles.chip}>
            {DB_ICONS[t.db_type] ?? '⚪'} {t.table_name}
            <button
              className={styles.removeBtn}
              onClick={() => onUnpin(t.id)}
              aria-label={`Remove ${t.table_name}`}
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <button className={styles.workbenchButton} onClick={onOpenWorkbench}>
        Open Workbench →
      </button>
    </div>
  )
}
