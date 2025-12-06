import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import App from './App.jsx'
import GamePage from './pages/GamePage.jsx'
import DataPage from './pages/DataPage.jsx'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <HelmetProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/games/:slug" element={<GamePage />} />
          <Route path="/data" element={<DataPage />} />
        </Routes>
      </BrowserRouter>
    </HelmetProvider>
  </StrictMode>
)
