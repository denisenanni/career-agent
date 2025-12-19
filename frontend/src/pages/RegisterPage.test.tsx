import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { RegisterPage } from './RegisterPage'
import { AuthContext } from '../contexts/AuthContext'

const mockNavigate = vi.fn()
const mockRegister = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: null }),
  }
})

const mockAuthContextValue = {
  user: null,
  login: vi.fn(),
  register: mockRegister,
  logout: vi.fn(),
  refreshUser: vi.fn(),
  loading: false,
}

function renderRegisterPage() {
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={mockAuthContextValue}>
        <RegisterPage />
      </AuthContext.Provider>
    </BrowserRouter>
  )
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render registration form', () => {
    renderRegisterPage()

    expect(screen.getByRole('heading', { name: /create your account/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('should show email validation error on blur with empty email', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    const emailInput = screen.getByLabelText(/email address/i)
    await user.click(emailInput)
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument()
    })
  })

  it('should show email validation error for invalid email format', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    const emailInput = screen.getByLabelText(/email address/i)
    await user.type(emailInput, 'invalid-email')
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
    })
  })

  it('should clear email error when valid email is entered', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    const emailInput = screen.getByLabelText(/email address/i)
    await user.type(emailInput, 'invalid-email')
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
    })

    await user.clear(emailInput)
    await user.type(emailInput, 'test@example.com')
    await user.tab()

    await waitFor(() => {
      expect(screen.queryByText('Please enter a valid email address')).not.toBeInTheDocument()
    })
  })

  it('should show password validation error for empty password', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    const passwordInput = screen.getByLabelText(/^password$/i)
    await user.click(passwordInput)
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Password is required')).toBeInTheDocument()
    })
  })

  it('should show password validation error for short password', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    const passwordInput = screen.getByLabelText(/^password$/i)
    await user.type(passwordInput, 'short')
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument()
    })
  })

  it('should clear password error when valid password is entered', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    const passwordInput = screen.getByLabelText(/^password$/i)
    await user.type(passwordInput, 'short')
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument()
    })

    await user.clear(passwordInput)
    await user.type(passwordInput, 'validpassword123')
    await user.tab()

    await waitFor(() => {
      expect(screen.queryByText('Password must be at least 8 characters')).not.toBeInTheDocument()
    })
  })

  it('should show confirm password validation error for empty confirmation', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    await user.click(confirmPasswordInput)
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Please confirm your password')).toBeInTheDocument()
    })
  })

  it('should show confirm password validation error when passwords do not match', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'different123')
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
    })
  })

  it('should clear confirm password error when passwords match', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'different123')
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
    })

    await user.clear(confirmPasswordInput)
    await user.type(confirmPasswordInput, 'password123')
    await user.tab()

    await waitFor(() => {
      expect(screen.queryByText('Passwords do not match')).not.toBeInTheDocument()
    })
  })

  it('should not submit form with validation errors', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    // Should show all validation errors
    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument()
      expect(screen.getByText('Password is required')).toBeInTheDocument()
      expect(screen.getByText('Please confirm your password')).toBeInTheDocument()
    })

    // Should not call register
    expect(mockRegister).not.toHaveBeenCalled()
  })

  it('should submit form with valid data', async () => {
    const user = userEvent.setup()
    mockRegister.mockResolvedValueOnce(undefined)

    renderRegisterPage()

    await user.type(screen.getByLabelText(/email address/i), 'test@example.com')
    await user.type(screen.getByLabelText(/^password$/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
    })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/profile', { replace: true })
    })
  })

  it('should show error message when registration fails', async () => {
    const user = userEvent.setup()
    mockRegister.mockRejectedValueOnce(new Error('Email already exists'))

    renderRegisterPage()

    await user.type(screen.getByLabelText(/email address/i), 'test@example.com')
    await user.type(screen.getByLabelText(/^password$/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument()
    })
  })

  it('should show loading state during registration', async () => {
    const user = userEvent.setup()
    mockRegister.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    renderRegisterPage()

    await user.type(screen.getByLabelText(/email address/i), 'test@example.com')
    await user.type(screen.getByLabelText(/^password$/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    // Button should be disabled during loading
    const submitButton = screen.getByRole('button', { name: /creating.../i })
    expect(submitButton).toBeDisabled()

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /creating.../i })).not.toBeInTheDocument()
    })
  })

  it('should have link to login page', () => {
    renderRegisterPage()

    const loginLink = screen.getByRole('link', { name: /sign in/i })
    expect(loginLink).toHaveAttribute('href', '/login')
  })
})
