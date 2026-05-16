import { Link } from 'react-router-dom'
import './SettingsInfoLink.css'

type SettingsInfoLinkProps = {
  label?: string
}

export function SettingsInfoLink({
  label = 'Configure GitHub repository and personal access token in Settings',
}: SettingsInfoLinkProps) {
  return (
    <Link
      to="/settings"
      className="settings-info-link"
      title={label}
      aria-label={label}
    >
      <svg
        className="settings-info-icon"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
          clipRule="evenodd"
        />
      </svg>
    </Link>
  )
}
