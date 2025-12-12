import { Outlet, NavLink } from 'react-router-dom'
import { Briefcase, Target, User, Home } from 'lucide-react'
import { clsx } from 'clsx'

const navItems = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/matches', label: 'Matches', icon: Target },
  { to: '/profile', label: 'Profile', icon: User },
]

export function Layout() {
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
          </div>
        </div>
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
