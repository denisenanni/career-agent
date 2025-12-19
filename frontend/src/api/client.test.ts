import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { apiFetch, APIError, buildQueryString } from './client'

describe('APIError', () => {
  it('should create an APIError with message, status, and code', () => {
    const error = new APIError('Test error', 400, 'BAD_REQUEST')
    expect(error.message).toBe('Test error')
    expect(error.status).toBe(400)
    expect(error.code).toBe('BAD_REQUEST')
    expect(error.name).toBe('APIError')
  })
})

describe('buildQueryString', () => {
  it('should build query string from params object', () => {
    const params = { foo: 'bar', baz: 123 }
    expect(buildQueryString(params)).toBe('?foo=bar&baz=123')
  })

  it('should handle array values', () => {
    const params = { tags: ['a', 'b', 'c'] }
    expect(buildQueryString(params)).toBe('?tags=a&tags=b&tags=c')
  })

  it('should skip undefined, null, and empty values', () => {
    const params = { foo: 'bar', baz: undefined, qux: null, empty: '' }
    expect(buildQueryString(params)).toBe('?foo=bar')
  })

  it('should return empty string for empty params', () => {
    expect(buildQueryString({})).toBe('')
  })
})

describe('apiFetch', () => {
  const originalFetch = global.fetch
  const mockFetch = vi.fn()

  beforeEach(() => {
    global.fetch = mockFetch
    localStorage.clear()
  })

  afterEach(() => {
    global.fetch = originalFetch
    mockFetch.mockReset()
  })

  it('should make successful GET request', async () => {
    const mockData = { id: 1, name: 'Test' }
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockData,
    })

    const result = await apiFetch('/api/test')

    expect(result).toEqual(mockData)
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/test',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    )
  })

  it('should add auth token when requiresAuth is true', async () => {
    localStorage.setItem('access_token', 'test-token')
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({}),
    })

    await apiFetch('/api/protected', { requiresAuth: true })

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/protected',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-token',
        }),
      })
    )
  })

  it('should throw error when auth token is missing and requiresAuth is true', async () => {
    await expect(apiFetch('/api/protected', { requiresAuth: true }))
      .rejects.toThrow('Please sign in to continue')
  })

  it('should handle FormData without Content-Type header', async () => {
    const formData = new FormData()
    formData.append('file', new Blob(['test']))

    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({}),
    })

    await apiFetch('/api/upload', {
      method: 'POST',
      body: formData,
    })

    const callArgs = mockFetch.mock.calls[0][1]
    expect(callArgs.headers['Content-Type']).toBeUndefined()
  })

  it('should handle 401 error and clear token for session expiry', async () => {
    localStorage.setItem('access_token', 'expired-token')
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Token has expired' }),
    })

    await expect(apiFetch('/api/test', { requiresAuth: true }))
      .rejects.toThrow('Your session has expired')

    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('should NOT clear token for login credential errors', async () => {
    localStorage.setItem('access_token', 'some-token')
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Incorrect email or password' }),
    })

    await expect(apiFetch('/api/auth/login', { method: 'POST' }))
      .rejects.toThrow('Incorrect email or password')

    // Token should NOT be cleared for login failures
    expect(localStorage.getItem('access_token')).toBe('some-token')
  })

  it('should parse FastAPI validation errors (422)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({
        detail: [
          { msg: 'value is not a valid email address' }
        ]
      }),
    })

    await expect(apiFetch('/api/test'))
      .rejects.toThrow('Please enter a valid email address')
  })

  it('should handle 422 with generic message for complex errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({
        detail: [
          { msg: 'Some complex validation error' }
        ]
      }),
    })

    await expect(apiFetch('/api/test'))
      .rejects.toThrow('Some complex validation error')
  })

  it('should handle 404 errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'User not found' }),
    })

    await expect(apiFetch('/api/users/999'))
      .rejects.toThrow('User not found')
  })

  it('should handle 429 rate limit errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      json: async () => ({ detail: 'Rate limit exceeded' }),
    })

    await expect(apiFetch('/api/test'))
      .rejects.toThrow('Too many requests')
  })

  it('should handle 500 server errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal server error' }),
    })

    await expect(apiFetch('/api/test'))
      .rejects.toThrow('A server error occurred')
  })

  it('should handle network errors', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

    await expect(apiFetch('/api/test'))
      .rejects.toThrow('Unable to connect to the server')
  })

  it('should handle responses with no content', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'text/plain' }),
    })

    const result = await apiFetch('/api/test')
    expect(result).toEqual({})
  })

  it('should handle string detail errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Invalid request format' }),
    })

    await expect(apiFetch('/api/test'))
      .rejects.toThrow('Invalid request format')
  })

  it('should handle errors with message field', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ message: 'Custom error message' }),
    })

    await expect(apiFetch('/api/test'))
      .rejects.toThrow('Custom error message')
  })

  it('should handle non-JSON error responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => { throw new Error('Not JSON') },
    })

    await expect(apiFetch('/api/test'))
      .rejects.toThrow('Access denied')
  })
})
