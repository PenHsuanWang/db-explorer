import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Workbench } from './Workbench'
import * as workbenchService from '../../services/workbenchService'

vi.mock('../../services/workbenchService')

describe('Workbench', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(workbenchService.fetchWorkbench).mockReturnValue(new Promise(() => {}))
  })

  it('renders empty state when no tables pinned', () => {
    render(
      <Workbench
        pinnedTables={[]}
        cleaningConfig={{}}
        onCleaningConfigChange={vi.fn()}
        onRemovePane={vi.fn()}
        onGoHome={vi.fn()}
      />
    )
    expect(screen.getByText(/No tables pinned yet/)).toBeInTheDocument()
  })

  it('renders pane headers for pinned tables', async () => {
    vi.mocked(workbenchService.fetchWorkbench).mockResolvedValue({
      panes: {
        p1: {
          columns: [{ name: 'id', type: 'INT' }],
          rows: [[{ column: 'id', type: 'INT', value: 1 }]],
        },
      },
    })
    render(
      <Workbench
        pinnedTables={[
          {
            id: 'p1',
            connection_id: 'conn1',
            connection_name: 'Oracle Finance',
            db_type: 'oracle',
            schema_name: 'FINANCE',
            table_name: 'MONTHLY_PROFIT',
            source_result: {
              id: 'r1',
              source_db: 'conn1',
              db_type: 'oracle',
              schema_name: 'FINANCE',
              table_name: 'MONTHLY_PROFIT',
              match_type: 'table_name',
              match_snippet: '',
              preview_columns: [],
            },
          },
        ]}
        cleaningConfig={{}}
        onCleaningConfigChange={vi.fn()}
        onRemovePane={vi.fn()}
        onGoHome={vi.fn()}
      />
    )
    expect(await screen.findByText('MONTHLY_PROFIT')).toBeInTheDocument()
  })
})
