import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { GameRepositoryProvider } from './presentation/context/GameRepositoryContext'
import GameListPage from './presentation/pages/GameListPage'
import GameDetailPage from './presentation/pages/GameDetailPage'

function App() {
  return (
    <GameRepositoryProvider>
      <Router>
        <Routes>
          <Route path="/" element={<GameListPage />} />
          <Route path="/game/:id" element={<GameDetailPage />} />
        </Routes>
      </Router>
    </GameRepositoryProvider>
  )
}

export default App
