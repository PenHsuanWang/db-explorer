import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Dock } from './Dock'
import type { PinnedTable } from '../../types/workbench'

const mockPinned: PinnedTable[] = [
  {
    id: 'p1',
    connection_id: 'oracle_finance',
    connection_name: 'Oracle Finance',
    db_type: 'oracle',
    schema_name: 'FINANCE',
    table_name: 'MONTHLY_PROFIT',
    source_result: {
      id: 'r1',
      source_db: 'oracle_finance',
      db_type: 'oracle',
      schema_name: 'FINANCE',
      table_name: 'MONTHLY_PROFIT',
      match_type: 'table_name',
      match_snippet: '',
      preview_columns: [],
    },
  },
]

describe('Dock', () => {
  it('renders nothing when no pinned tables', () => {
    const { container } = render(
      <Dock pinnedTables={[]} onUnpin={vi.fn()} onOpenWorkbench={vi.fn()} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders pinned table chip', () => {
    render(
      <Dock pinnedTables={mockPinned} onUnpin={vi.fn()} onOpenWorkbench={vi.fn()} />
    )
    expect(screen.getByText(/MONTHLY_PROFIT/)).toBeInTheDocument()
  })

  it('calls onOpenWorkbench when button clicked', () => {
    const onOpen = vi.fn()
    render(<Dock pinnedTables={mockPinned} onUnpin={vi.fn()} onOpenWorkbench={onOpen} />)
    fireEvent.click(screen.getByText(/Open Workbench/))
    expect(onOpen).toHaveBeenCalled()
  })
})
