import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { User } from '../api/client'
import './UserMenu.css'

type UserMenuProps = {
  user: User
  onLogout: () => void
}

function getInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
}

export function UserMenu({ user, onLogout }: UserMenuProps) {
  const [open, setOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!open) return

    const handlePointerDown = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }

    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [open])

  const handleLogout = () => {
    setOpen(false)
    onLogout()
    navigate('/welcome')
  }

  return (
    <div className="user-menu" ref={menuRef}>
      <button
        type="button"
        className="user-menu-trigger"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
      >
        <span className="user-avatar" aria-hidden="true">
          {getInitials(user.full_name)}
        </span>
        <span className="user-menu-name">{user.full_name}</span>
        <svg className="user-menu-chevron" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.94a.75.75 0 111.08 1.04l-4.24 4.5a.75.75 0 01-1.08 0l-4.24-4.5a.75.75 0 01.02-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {open && (
        <div className="user-menu-panel" role="menu">
          <div className="user-menu-header">
            <span className="user-avatar user-avatar-lg">{getInitials(user.full_name)}</span>
            <div className="user-menu-meta">
              <span className="user-menu-fullname">{user.full_name}</span>
              <span className="user-menu-email">{user.email}</span>
            </div>
          </div>
          <div className="user-menu-divider" />
          <Link
            to="/settings"
            className="user-menu-item"
            role="menuitem"
            onClick={() => setOpen(false)}
          >
            Settings
          </Link>
          <button
            type="button"
            className="user-menu-item user-menu-item-danger"
            role="menuitem"
            onClick={handleLogout}
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}
