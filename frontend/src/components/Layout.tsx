import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Layout.css'

export function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="layout">
      <header className="topbar">
        <Link to={user ? '/dashboard' : '/'} className="brand">
          <span className="brand-mark">QA</span>
          <span className="brand-text">Quality Assistance</span>
        </Link>

        <nav className="nav">
          {user ? (
            <>
              <NavLink to="/dashboard" className="nav-link">
                Workspace
              </NavLink>
              <NavLink to="/about" className="nav-link">
                About
              </NavLink>
              <span className="user-chip">{user.full_name}</span>
              <button type="button" className="btn btn-ghost" onClick={logout}>
                Sign out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/about" className="nav-link">
                About
              </NavLink>
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
