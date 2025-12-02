import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App.jsx'
import DataViewer from './DataViewer.jsx'
import GamePage from './pages/GamePage.jsx' // Import GamePage
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/data" element={<DataViewer />} />
        <Route path="/games/:slug" element={<GamePage />} /> {/* Add GamePage route */}
      </Routes>
    </BrowserRouter>
  </StrictMode>
)
