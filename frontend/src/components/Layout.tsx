import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Briefcase, Target, User, Home, LogOut, LogIn, TrendingUp, FileText, Menu, X } from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '../contexts/AuthContext'

const navItems = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/my-jobs', label: 'My Jobs', icon: FileText },
  { to: '/matches', label: 'Matches', icon: Target },
  { to: '/insights', label: 'Insights', icon: TrendingUp },
  { to: '/profile', label: 'Profile', icon: User },
]

export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
    setMobileMenuOpen(false)
  }

  const closeMobileMenu = () => setMobileMenuOpen(false)

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <span className="text-xl font-bold text-indigo-600">
                  Career Agent
                </span>
              </div>
              {/* Desktop Navigation */}
              <nav className="hidden sm:ml-8 sm:flex sm:space-x-4">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      clsx(
                        'inline-flex items-center px-3 py-2 text-sm font-medium rounded-md',
                        isActive
                          ? 'bg-indigo-100 text-indigo-700'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                      )
                    }
                  >
                    <item.icon className="w-4 h-4 mr-2" />
                    {item.label}
                  </NavLink>
                ))}
              </nav>
            </div>
            <div className="flex items-center gap-2">
              {/* Desktop Auth */}
              <div className="hidden sm:flex items-center gap-4">
                {user ? (
                  <>
                    <span className="text-sm text-gray-600 truncate max-w-[150px]">{user.email}</span>
                    <button
                      onClick={handleLogout}
                      className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Logout
                    </button>
                  </>
                ) : (
                  <NavLink
                    to="/login"
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 rounded-md"
                  >
                    <LogIn className="w-4 h-4 mr-2" />
                    Login
                  </NavLink>
                )}
              </div>
              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="sm:hidden inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="sm:hidden border-t border-gray-200">
            <nav className="px-2 pt-2 pb-3 space-y-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={closeMobileMenu}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center px-3 py-2 text-base font-medium rounded-md',
                      isActive
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    )
                  }
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.label}
                </NavLink>
              ))}
              <div className="border-t border-gray-200 pt-4 pb-3">
                {user ? (
                  <>
                    <div className="px-3 py-2">
                      <p className="text-sm font-medium text-gray-900 truncate">{user.email}</p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center px-3 py-2 text-base font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 rounded-md"
                    >
                      <LogOut className="w-5 h-5 mr-3" />
                      Logout
                    </button>
                  </>
                ) : (
                  <NavLink
                    to="/login"
                    onClick={closeMobileMenu}
                    className="flex items-center px-3 py-2 text-base font-medium text-indigo-600 hover:bg-indigo-50 rounded-md"
                  >
                    <LogIn className="w-5 h-5 mr-3" />
                    Login
                  </NavLink>
                )}
              </div>
            </nav>
          </div>
        )}
      </header>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Outlet />
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
          Career Agent &copy; {new Date().getFullYear()}
        </div>
      </footer>
    </div>
  )
}
