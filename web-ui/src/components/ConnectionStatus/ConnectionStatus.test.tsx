import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConnectionStatus } from './ConnectionStatus'
import * as connectionService from '../../services/connectionService'

vi.mock('../../services/connectionService')

describe('ConnectionStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state', () => {
    vi.mocked(connectionService.getConnections).mockReturnValue(new Promise(() => {}))
    render(<ConnectionStatus />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders connections', async () => {
    vi.mocked(connectionService.getConnections).mockResolvedValue({
      connections: [
        {
          id: '1',
          name: 'Demo',
          db_type: 'mock',
          host: 'localhost',
          port: 0,
          database: 'demo',
          status: 'connected',
        },
      ],
    })
    render(<ConnectionStatus />)
    expect(await screen.findByText(/Demo/)).toBeInTheDocument()
  })
})
