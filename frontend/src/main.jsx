import { StrictMode, Suspense, lazy } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'
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
        path: '/games/hackclad',
        element: <Navigate to="/games/hack-clad" replace />,
      },
      {
        path: '/games/:slug',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <GamePage />
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
