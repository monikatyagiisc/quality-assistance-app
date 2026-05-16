import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

const PAGE_TITLES: Record<string, string> = {
  '/welcome': 'Quality Assistance',
  '/login': 'Sign in · Quality Assistance',
  '/register': 'Create account · Quality Assistance',
  '/dashboard': 'Workspace · Quality Assistance',
  '/about': 'About · Quality Assistance',
}

const DEFAULT_TITLE = 'Quality Assistance'

export function usePageTitle() {
  const { pathname } = useLocation()

  useEffect(() => {
    document.title = PAGE_TITLES[pathname] ?? DEFAULT_TITLE
  }, [pathname])
}
