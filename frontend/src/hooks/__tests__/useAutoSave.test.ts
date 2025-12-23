import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAutoSave } from '../useAutoSave'

describe('useAutoSave', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should not trigger save on initial mount', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const initialData = { name: 'John', email: 'john@example.com' }

    renderHook(() =>
      useAutoSave({
        data: initialData,
        onSave,
        debounceMs: 1000,
        enabled: true,
      })
    )

    // Wait for debounce
    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(onSave).not.toHaveBeenCalled()
  })

  it('should not trigger save when enabled becomes true for the first time', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const initialData = { name: 'John' }

    // Start with enabled=false
    const { rerender } = renderHook(
      ({ data, enabled }) =>
        useAutoSave({
          data,
          onSave,
          debounceMs: 1000,
          enabled,
        }),
      { initialProps: { data: initialData, enabled: false } }
    )

    // Change data while disabled
    const newData = { name: 'Jane' }
    rerender({ data: newData, enabled: false })

    // Now enable - this should NOT trigger save (captures baseline)
    rerender({ data: newData, enabled: true })

    // Wait for debounce
    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(onSave).not.toHaveBeenCalled()
  })

  it('should trigger save when data changes after being enabled', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const initialData = { name: 'John' }

    const { rerender } = renderHook(
      ({ data, enabled }) =>
        useAutoSave({
          data,
          onSave,
          debounceMs: 1000,
          enabled,
        }),
      { initialProps: { data: initialData, enabled: true } }
    )

    // Change data after initial mount
    const newData = { name: 'Jane' }
    rerender({ data: newData, enabled: true })

    // Wait for debounce
    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(onSave).toHaveBeenCalledTimes(1)
    expect(onSave).toHaveBeenCalledWith(newData)
  })

  it('should trigger save when data changes after enabled becomes true', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const initialData = { name: 'John' }

    // Start with enabled=false
    const { rerender } = renderHook(
      ({ data, enabled }) =>
        useAutoSave({
          data,
          onSave,
          debounceMs: 1000,
          enabled,
        }),
      { initialProps: { data: initialData, enabled: false } }
    )

    // Now enable with same data
    rerender({ data: initialData, enabled: true })

    // Wait for debounce - should NOT save (baseline captured)
    act(() => {
      vi.advanceTimersByTime(2000)
    })
    expect(onSave).not.toHaveBeenCalled()

    // Now change data
    const newData = { name: 'Jane' }
    rerender({ data: newData, enabled: true })

    // Wait for debounce - SHOULD save now
    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(onSave).toHaveBeenCalledTimes(1)
    expect(onSave).toHaveBeenCalledWith(newData)
  })

  it('should not save while disabled', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const initialData = { name: 'John' }

    const { rerender } = renderHook(
      ({ data, enabled }) =>
        useAutoSave({
          data,
          onSave,
          debounceMs: 1000,
          enabled,
        }),
      { initialProps: { data: initialData, enabled: false } }
    )

    // Change data multiple times while disabled
    rerender({ data: { name: 'Jane' }, enabled: false })
    rerender({ data: { name: 'Bob' }, enabled: false })

    // Wait for debounce
    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(onSave).not.toHaveBeenCalled()
  })

  it('should debounce multiple rapid changes', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const initialData = { name: 'John' }

    const { rerender } = renderHook(
      ({ data }) =>
        useAutoSave({
          data,
          onSave,
          debounceMs: 1000,
          enabled: true,
        }),
      { initialProps: { data: initialData } }
    )

    // Rapid changes
    rerender({ data: { name: 'Jane' } })
    act(() => {
      vi.advanceTimersByTime(500)
    })
    rerender({ data: { name: 'Bob' } })
    act(() => {
      vi.advanceTimersByTime(500)
    })
    rerender({ data: { name: 'Alice' } })

    // Wait for debounce
    act(() => {
      vi.advanceTimersByTime(2000)
    })

    // Should only save once with final value
    expect(onSave).toHaveBeenCalledTimes(1)
    expect(onSave).toHaveBeenCalledWith({ name: 'Alice' })
  })

  it('should return correct status during save', async () => {
    let resolvePromise: () => void
    const onSave = vi.fn().mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolvePromise = resolve
        })
    )

    const { result, rerender } = renderHook(
      ({ data }) =>
        useAutoSave({
          data,
          onSave,
          debounceMs: 1000,
          enabled: true,
        }),
      { initialProps: { data: { name: 'John' } } }
    )

    expect(result.current.status).toBe('idle')

    // Trigger save
    rerender({ data: { name: 'Jane' } })
    act(() => {
      vi.advanceTimersByTime(1500)
    })

    expect(result.current.status).toBe('saving')

    // Complete save
    await act(async () => {
      resolvePromise!()
    })

    expect(result.current.status).toBe('saved')
  })
})
