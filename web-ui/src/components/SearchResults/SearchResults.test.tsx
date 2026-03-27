import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SearchResults } from './SearchResults'
import type { SearchResult } from '../../types/api'

const mockResults: SearchResult[] = [
  {
    id: 'r1',
    source_db: 'oracle_finance',
    db_type: 'oracle',
    schema_name: 'FINANCE',
    table_name: 'MONTHLY_PROFIT',
    match_type: 'table_name',
    match_snippet: 'Found profit',
    preview_columns: [],
  },
]

describe('SearchResults', () => {
  it('renders results count', () => {
    render(
      <SearchResults
        query="profit"
        results={mockResults}
        loading={false}
        pinnedTables={[]}
        onBack={vi.fn()}
        onPeek={vi.fn()}
        onPin={vi.fn()}
        onUnpin={vi.fn()}
        onOpenWorkbench={vi.fn()}
      />
    )
    expect(screen.getByText('(1 results)')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(
      <SearchResults
        query="profit"
        results={[]}
        loading={true}
        pinnedTables={[]}
        onBack={vi.fn()}
        onPeek={vi.fn()}
        onPin={vi.fn()}
        onUnpin={vi.fn()}
        onOpenWorkbench={vi.fn()}
      />
    )
    expect(screen.getByText('Searching...')).toBeInTheDocument()
  })
})
