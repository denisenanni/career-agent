import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { AuthContext } from '../contexts/AuthContext'

const mockNavigate = vi.fn()
const mockLogin = vi.fn()

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
  login: mockLogin,
  register: vi.fn(),
  logout: vi.fn(),
  refreshUser: vi.fn(),
  loading: false,
}

function renderLoginPage() {
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={mockAuthContextValue}>
        <LoginPage />
      </AuthContext.Provider>
    </BrowserRouter>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render login form', () => {
    renderLoginPage()

    expect(screen.getByRole('heading', { name: /sign in to your account/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('should show email validation error on blur with empty email', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    const emailInput = screen.getByLabelText(/email address/i)
    await user.click(emailInput)
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument()
    })
  })

  it('should show email validation error for invalid email format', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    const emailInput = screen.getByLabelText(/email address/i)
    await user.type(emailInput, 'not-an-email')
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
    })
  })

  it('should clear email error when valid email is entered', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    const emailInput = screen.getByLabelText(/email address/i)
    await user.type(emailInput, 'not-an-email')
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
    })

    await user.clear(emailInput)
    await user.type(emailInput, 'user@example.com')
    await user.tab()

    await waitFor(() => {
      expect(screen.queryByText('Please enter a valid email address')).not.toBeInTheDocument()
    })
  })

  it('should submit form with valid credentials', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValueOnce(undefined)

    renderLoginPage()

    await user.type(screen.getByLabelText(/email address/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: 'password123',
      })
    })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/profile', { replace: true })
    })
  })

  it('should show error message when login fails', async () => {
    const user = userEvent.setup()
    mockLogin.mockRejectedValueOnce(new Error('Incorrect email or password'))

    renderLoginPage()

    await user.type(screen.getByLabelText(/email address/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('Incorrect email or password')).toBeInTheDocument()
    })
  })

  it('should show loading state during login', async () => {
    const user = userEvent.setup()
    mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    renderLoginPage()

    await user.type(screen.getByLabelText(/email address/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    // Button should show loading state
    const submitButton = screen.getByRole('button', { name: /signing in.../i })
    expect(submitButton).toBeDisabled()

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /signing in.../i })).not.toBeInTheDocument()
    })
  })

  it('should have link to register page', () => {
    renderLoginPage()

    const registerLink = screen.getByRole('link', { name: /create a new account/i })
    expect(registerLink).toHaveAttribute('href', '/register')
  })

  it('should allow form submission without email validation if email is valid', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValueOnce(undefined)

    renderLoginPage()

    // Type valid email without triggering blur validation
    await user.type(screen.getByLabelText(/email address/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    // Should not show email error
    expect(screen.queryByText('Please enter a valid email address')).not.toBeInTheDocument()

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled()
    })
  })

  it('should clear previous error when attempting new login', async () => {
    const user = userEvent.setup()
    mockLogin.mockRejectedValueOnce(new Error('First error'))

    renderLoginPage()

    await user.type(screen.getByLabelText(/email address/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('First error')).toBeInTheDocument()
    })

    // Clear error by trying again
    mockLogin.mockResolvedValueOnce(undefined)
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.queryByText('First error')).not.toBeInTheDocument()
    })
  })
})
