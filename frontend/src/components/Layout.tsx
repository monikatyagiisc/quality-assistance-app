import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { usePageTitle } from '../hooks/usePageTitle'
import { UserMenu } from './UserMenu'
import './Layout.css'

export function Layout() {
  const { user, logout } = useAuth()
  usePageTitle()

  return (
    <div className="layout">
      <header className="topbar">
        <div className="topbar-start">
          <Link to={user ? '/dashboard' : '/'} className="brand">
            <span className="brand-mark">QA</span>
            <span className="brand-text">Quality Assistance</span>
          </Link>

          <nav className="nav nav-left" aria-label="Main">
            {user && (
              <NavLink to="/dashboard" className="nav-link">
                Workspace
              </NavLink>
            )}
            <NavLink to="/about" className="nav-link">
              About
            </NavLink>
          </nav>
        </div>

        <nav className="nav nav-right" aria-label="Account">
          {user ? (
            <UserMenu user={user} onLogout={logout} />
          ) : (
            <>
              <NavLink to="/login" className="nav-link">
                Sign in
              </NavLink>
              <NavLink to="/register" className="btn btn-primary">
                Get started
              </NavLink>
            </>
          )}
        </nav>
      </header>

      <main className="main">
        <Outlet />
      </main>

      <footer className="footer">
        <p>AI-powered STLC assistant · Final year project</p>
      </footer>
    </div>
  )
}
