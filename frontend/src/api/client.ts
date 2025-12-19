const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message)
    this.name = 'APIError'
  }
}

interface FetchOptions extends RequestInit {
  requiresAuth?: boolean
}

/**
 * Centralized fetch wrapper with improved error handling
 */
export async function apiFetch<T = any>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { requiresAuth = false, headers = {}, body, ...fetchOptions } = options

  // Build headers
  const requestHeaders: Record<string, string> = {
    ...headers as Record<string, string>,
  }

  // Only add Content-Type if not FormData (FormData sets its own boundary)
  if (!(body instanceof FormData)) {
    requestHeaders['Content-Type'] = 'application/json'
  }

  // Add auth token if required
  if (requiresAuth) {
    const token = localStorage.getItem('access_token')
    if (!token) {
      throw new APIError('Please sign in to continue', 401, 'UNAUTHORIZED')
    }
    requestHeaders['Authorization'] = `Bearer ${token}`
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers: requestHeaders,
      body,
    })

    // Handle successful responses
    if (response.ok) {
      // Check if response has content
      const contentType = response.headers.get('content-type')
      if (contentType?.includes('application/json')) {
        return await response.json()
      }
      // Return empty object for no-content responses
      return {} as T
    }

    // Handle error responses
    await handleErrorResponse(response)

    // This line should never be reached, but TypeScript requires it
    throw new APIError('An unexpected error occurred')
  } catch (error) {
    // Handle network errors
    if (error instanceof APIError) {
      throw error
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError(
        'Unable to connect to the server. Please check your internet connection and try again.',
        0,
        'NETWORK_ERROR'
      )
    }

    throw new APIError(
      error instanceof Error ? error.message : 'An unexpected error occurred',
      0,
      'UNKNOWN_ERROR'
    )
  }
}

async function handleErrorResponse(response: Response): Promise<never> {
  const status = response.status
  let errorMessage = 'An error occurred'
  let errorCode = 'UNKNOWN_ERROR'

  try {
    const errorData = await response.json()

    // Handle FastAPI validation errors (422)
    if (status === 422 && Array.isArray(errorData.detail)) {
      // Extract first validation error message
      const firstError = errorData.detail[0]
      if (firstError?.msg) {
        errorMessage = firstError.msg
        // Clean up technical validation messages
        if (errorMessage.includes('value is not a valid email')) {
          errorMessage = 'Please enter a valid email address'
        }
      } else {
        errorMessage = 'Please check your input and try again.'
      }
      errorCode = 'VALIDATION_ERROR'
    } else if (typeof errorData.detail === 'string') {
      // Handle simple string detail
      errorMessage = errorData.detail
    } else if (errorData.message) {
      errorMessage = errorData.message
    }

    if (errorData.code) {
      errorCode = errorData.code
    }
  } catch {
    // If response body is not JSON, use status-based messages
    errorMessage = getStatusMessage(status)
  }

  // Add context based on status code (only if not already handled above)
  switch (status) {
    case 400:
      errorCode = errorCode === 'UNKNOWN_ERROR' ? 'BAD_REQUEST' : errorCode
      break
    case 401:
      errorCode = 'UNAUTHORIZED'
      // Only override message and clear token if it's a session expiry (not login failure)
      if (errorMessage === 'An error occurred' || errorMessage.toLowerCase().includes('token') || errorMessage.toLowerCase().includes('session')) {
        errorMessage = 'Your session has expired. Please sign in again.'
        // Clear token only for actual session expiry, not login failures
        localStorage.removeItem('access_token')
      }
      // For login failures (incorrect credentials), keep the original message
      break
    case 403:
      errorCode = 'FORBIDDEN'
      if (errorMessage === 'An error occurred') {
        errorMessage = 'You don\'t have permission to perform this action.'
      }
      break
    case 404:
      errorCode = 'NOT_FOUND'
      if (errorMessage === 'An error occurred') {
        errorMessage = 'The requested resource was not found.'
      }
      break
    case 422:
      // Already handled above
      if (errorCode === 'UNKNOWN_ERROR') {
        errorCode = 'VALIDATION_ERROR'
      }
      break
    case 429:
      errorCode = 'RATE_LIMIT'
      errorMessage = 'Too many requests. Please wait a moment and try again.'
      break
    case 500:
      errorCode = 'SERVER_ERROR'
      errorMessage = 'A server error occurred. Our team has been notified.'
      break
    case 503:
      errorCode = 'SERVICE_UNAVAILABLE'
      errorMessage = 'Service temporarily unavailable. Please try again in a few moments.'
      break
  }

  throw new APIError(errorMessage, status, errorCode)
}

function getStatusMessage(status: number): string {
  const messages: Record<number, string> = {
    400: 'Invalid request. Please check your input.',
    401: 'Authentication required. Please sign in.',
    403: 'Access denied.',
    404: 'Resource not found.',
    422: 'Validation error. Please check your input.',
    429: 'Too many requests. Please slow down.',
    500: 'Server error. Please try again later.',
    503: 'Service unavailable. Please try again later.',
  }

  return messages[status] || `Request failed with status ${status}`
}

/**
 * Helper to build query string from params object
 */
export function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(v => searchParams.append(key, String(v)))
      } else {
        searchParams.append(key, String(value))
      }
    }
  })

  const queryString = searchParams.toString()
  return queryString ? `?${queryString}` : ''
}
