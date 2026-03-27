import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { GlobalSearch } from './GlobalSearch'

describe('GlobalSearch', () => {
  it('renders search input', () => {
    render(<GlobalSearch onSearch={vi.fn()} />)
    expect(screen.getByPlaceholderText(/Search tables/)).toBeInTheDocument()
  })

  it('calls onSearch when Enter is pressed', () => {
    const onSearch = vi.fn()
    render(<GlobalSearch onSearch={onSearch} />)
    const input = screen.getByPlaceholderText(/Search tables/)
    fireEvent.change(input, { target: { value: 'profit' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onSearch).toHaveBeenCalledWith('profit', false)
  })

  it('calls onSearch when Search button is clicked', () => {
    const onSearch = vi.fn()
    render(<GlobalSearch onSearch={onSearch} />)
    const input = screen.getByPlaceholderText(/Search tables/)
    fireEvent.change(input, { target: { value: 'revenue' } })
    fireEvent.click(screen.getByText('Search'))
    expect(onSearch).toHaveBeenCalledWith('revenue', false)
  })

  it('shows deep search warning when toggled', () => {
    render(<GlobalSearch onSearch={vi.fn()} />)
    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)
    expect(screen.getByText(/This may take longer/)).toBeInTheDocument()
  })
})
