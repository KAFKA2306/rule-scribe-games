import { StrictMode, Suspense, lazy } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import App from './App.jsx'
import './index.css'
import './layout.css'
import './game-detail-palette.css'
import './ui-palette.css'
import './uiux-accessibility.css'
import './auth-control.css'

const GamePage = lazy(() => import('./pages/GamePage.jsx'))
const DataPage = lazy(() => import('./pages/DataPage.jsx'))
const ListsPage = lazy(() => import('./pages/ListsPage.jsx'))

import { AuthProvider } from './auth/AuthContext.jsx'
import AppShell from './components/AppShell.jsx'
import LoadingFallback from './components/LoadingFallback.jsx'
import { installMobileFilterFocus } from './lib/mobileFilterFocus.js'

installMobileFilterFocus()

function readSsrGameData() {
  const element = document.getElementById('ssr-game-data')
  if (!element) return null

  try {
    const game = JSON.parse(element.textContent || '')
    const routeSlug = window.location.pathname.match(/^\/games\/([^/]+)$/)?.[1]
    return game && game.slug === routeSlug ? game : null
  } catch (error) {
    console.error('Could not parse server-rendered game data:', error)
    return null
  } finally {
    element.remove()
  }
}

const initialSsrGame = readSsrGameData()

const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      {
        path: '/',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <App />
          </Suspense>
        ),
      },
      {
        path: '/games/:slug',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <GamePage initialGame={initialSsrGame} />
          </Suspense>
        ),
      },
      {
        path: '/lists',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <ListsPage />
          </Suspense>
        ),
      },
      {
        path: '/data',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <DataPage />
          </Suspense>
        ),
      },
    ],
  },
])

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <HelmetProvider>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </HelmetProvider>
  </StrictMode>,
)
