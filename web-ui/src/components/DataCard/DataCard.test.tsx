import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DataCard } from './DataCard'
import type { SearchResult } from '../../types/api'

const mockResult: SearchResult = {
  id: 'r1',
  source_db: 'oracle_finance',
  db_type: 'oracle',
  schema_name: 'FINANCE',
  table_name: 'MONTHLY_PROFIT',
  match_type: 'table_name',
  match_snippet: 'Found "profit" in table name',
  preview_columns: [
    { name: 'id', type: 'INT' },
    { name: 'date', type: 'DATE' },
    { name: 'amount', type: 'DECIMAL' },
  ],
}

describe('DataCard', () => {
  it('renders table name', () => {
    render(
      <DataCard
        result={mockResult}
        isPinned={false}
        onPeek={vi.fn()}
        onPin={vi.fn()}
        onUnpin={vi.fn()}
      />
    )
    expect(screen.getByText('MONTHLY_PROFIT')).toBeInTheDocument()
  })

  it('shows Pin + button when not pinned', () => {
    render(
      <DataCard
        result={mockResult}
        isPinned={false}
        onPeek={vi.fn()}
        onPin={vi.fn()}
        onUnpin={vi.fn()}
      />
    )
    expect(screen.getByText('Pin +')).toBeInTheDocument()
  })

  it('shows ✓ Pinned when pinned', () => {
    render(
      <DataCard
        result={mockResult}
        isPinned={true}
        onPeek={vi.fn()}
        onPin={vi.fn()}
        onUnpin={vi.fn()}
      />
    )
    expect(screen.getByText('✓ Pinned')).toBeInTheDocument()
  })

  it('calls onPeek when Peek clicked', () => {
    const onPeek = vi.fn()
    render(
      <DataCard
        result={mockResult}
        isPinned={false}
        onPeek={onPeek}
        onPin={vi.fn()}
        onUnpin={vi.fn()}
      />
    )
    fireEvent.click(screen.getByText('👁 Peek'))
    expect(onPeek).toHaveBeenCalledWith(mockResult)
  })
})
