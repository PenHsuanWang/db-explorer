import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PeekModal } from './PeekModal'
import type { SearchResult } from '../../types/api'
import * as peekService from '../../services/peekService'

vi.mock('../../services/peekService')

const mockResult: SearchResult = {
  id: 'r1',
  source_db: 'oracle_finance',
  db_type: 'oracle',
  schema_name: 'FINANCE',
  table_name: 'MONTHLY_PROFIT',
  match_type: 'table_name',
  match_snippet: 'Found profit',
  preview_columns: [],
}

describe('PeekModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders title', () => {
    vi.mocked(peekService.peek).mockReturnValue(new Promise(() => {}))
    render(<PeekModal result={mockResult} isPinned={false} onPin={vi.fn()} onClose={vi.fn()} />)
    expect(screen.getByText(/MONTHLY_PROFIT/)).toBeInTheDocument()
  })

  it('shows loading state', () => {
    vi.mocked(peekService.peek).mockReturnValue(new Promise(() => {}))
    render(<PeekModal result={mockResult} isPinned={false} onPin={vi.fn()} onClose={vi.fn()} />)
    expect(screen.getByText(/Loading sample data/)).toBeInTheDocument()
  })

  it('shows data when loaded', async () => {
    vi.mocked(peekService.peek).mockResolvedValue({
      columns: [{ name: 'id', type: 'INT' }],
      rows: [[{ column: 'id', type: 'INT', value: 42 }]],
    })
    render(<PeekModal result={mockResult} isPinned={false} onPin={vi.fn()} onClose={vi.fn()} />)
    expect(await screen.findByText('42')).toBeInTheDocument()
  })

  it('shows NULL placeholder for null values', async () => {
    vi.mocked(peekService.peek).mockResolvedValue({
      columns: [{ name: 'val', type: 'TEXT' }],
      rows: [[{ column: 'val', type: 'TEXT', value: null }]],
    })
    render(<PeekModal result={mockResult} isPinned={false} onPin={vi.fn()} onClose={vi.fn()} />)
    expect(await screen.findByText('<NULL>')).toBeInTheDocument()
  })
})
