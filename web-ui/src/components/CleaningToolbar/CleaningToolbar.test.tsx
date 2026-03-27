import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CleaningToolbar } from './CleaningToolbar'

describe('CleaningToolbar', () => {
  it('renders all options', () => {
    render(<CleaningToolbar config={{}} onChange={vi.fn()} />)
    expect(screen.getByText('Normalize Dates')).toBeInTheDocument()
    expect(screen.getByText('Trim Spaces')).toBeInTheDocument()
    expect(screen.getByText('Hide Nulls')).toBeInTheDocument()
  })

  it('calls onChange when toggle clicked', () => {
    const onChange = vi.fn()
    render(<CleaningToolbar config={{ hide_null_values: false }} onChange={onChange} />)
    const hideNullsCheckbox = screen.getAllByRole('checkbox')[2]
    fireEvent.click(hideNullsCheckbox)
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ hide_null_values: true }))
  })
})
