import { StrictMode, Suspense, lazy } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import App from './App.jsx'
import './index.css'

const GamePage = lazy(() => import('./pages/GamePage.jsx'))
const DataPage = lazy(() => import('./pages/DataPage.jsx'))

import LoadingFallback from './components/LoadingFallback.jsx'
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
