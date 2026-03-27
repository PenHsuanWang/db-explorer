import type { CleaningConfig } from '../../types/api'
import styles from './CleaningToolbar.module.css'

interface CleaningToolbarProps {
  config: CleaningConfig
  onChange: (config: CleaningConfig) => void
}

export function CleaningToolbar({ config, onChange }: CleaningToolbarProps) {
  const update = (partial: Partial<CleaningConfig>) => {
    onChange({ ...config, ...partial })
  }

  return (
    <div className={styles.toolbar}>
      <span className={styles.label}>Cleaning Engine:</span>

      <label className={styles.option}>
        <input
          type="checkbox"
          checked={config.date_format === 'ISO8601'}
          onChange={(e) => update({ date_format: e.target.checked ? 'ISO8601' : 'raw' })}
        />
        <span>Normalize Dates</span>
      </label>

      <label className={styles.option}>
        <input
          type="checkbox"
          checked={config.trim_strings ?? false}
          onChange={(e) => update({ trim_strings: e.target.checked })}
        />
        <span>Trim Spaces</span>
      </label>

      <label className={styles.option}>
        <input
          type="checkbox"
          checked={config.hide_null_values ?? false}
          onChange={(e) => update({ hide_null_values: e.target.checked })}
        />
        <span>Hide Nulls</span>
      </label>
    </div>
  )
}
