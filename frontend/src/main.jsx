import { StrictMode, Suspense, lazy } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import App from './App.jsx'
import './index.css'

const GamePage = lazy(() => import('./pages/GamePage.jsx'))
const DataPage = lazy(() => import('./pages/DataPage.jsx'))

const LoadingFallback = () => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'var(--bg-primary, #0b1221)',
    }}
  >
    <p style={{ color: 'var(--text-primary, #fff)' }}>読み込み中...</p>
  </div>
)
const router = createBrowserRouter([
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
        <GamePage />
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
])

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <HelmetProvider>
      <RouterProvider router={router} />
    </HelmetProvider>
  </StrictMode>
)
