import React, { useState } from 'react'

const Markdown = ({ content }) => (
  <div
    className="prose prose-sm max-w-none text-gray-700"
    dangerouslySetInnerHTML={{
      __html: content
        .replace(/\n/g, '<br/>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'),
    }}
  />
)

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedGame, setSelectedGame] = useState(null)
  const [summary, setSummary] = useState(null)

  const api = async (url, body) => {
    setLoading(true)
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    setLoading(false)
    return await res.json()
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setResults([])
    setSelectedGame(null)
    setSummary(null)
    const data = await api('/api/search', { query })
    if (data) setResults(data)
  }

  const handleSummarize = async () => {
    if (!selectedGame) return
    const data = await api('/api/summarize', {
      text: selectedGame.rules_content,
    })
    if (data) setSummary(data.summary)
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-indigo-600 tracking-tight">
              RuleScribe
            </span>
            <span className="text-xs font-medium bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full">
              Minimal
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-4">
            Master Any Board Game
          </h1>
          <p className="text-lg text-gray-600">
            Instantly find rules, get AI-powered summaries, and start playing
            faster.
          </p>
        </div>

        <div className="max-w-3xl mx-auto mb-10">
          <form onSubmit={handleSearch} className="relative">
            <input
              type="text"
              className="block w-full pl-4 pr-24 py-4 border border-gray-300 rounded-xl text-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none shadow-sm"
              placeholder="Search (e.g., Catan)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button
              type="submit"
              disabled={loading}
              className="absolute inset-y-2 right-2 px-6 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg disabled:opacity-50"
            >
              {loading ? '...' : 'Search'}
            </button>
          </form>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 space-y-4">
            <h2 className="text-lg font-semibold">
              Results{' '}
              {results.length > 0 && (
                <span className="text-sm text-gray-500">
                  ({results.length})
                </span>
              )}
            </h2>
            {results.length === 0 && !loading && query && (
              <div className="p-8 text-center border-2 border-dashed rounded-xl text-gray-500">
                No games found via DB.
              </div>
            )}
            {results.map((game) => (
              <div
                key={game.id}
                onClick={() => {
                  setSelectedGame(game)
                  setSummary(null)
                }}
                className={`p-4 rounded-xl border cursor-pointer hover:shadow-md transition-all ${selectedGame?.id === game.id ? 'bg-indigo-50 border-indigo-200 ring-1' : 'bg-white hover:border-indigo-300'}`}
              >
                <h3 className="font-bold text-gray-800">{game.title}</h3>
                <p className="text-sm text-gray-600 line-clamp-2">
                  {game.description}
                </p>
              </div>
            ))}
          </div>

          <div className="lg:col-span-2">
            {selectedGame ? (
              <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
                {selectedGame.image_url && (
                  <div className="h-64 bg-gray-100 relative">
                    <img
                      src={selectedGame.image_url}
                      alt={selectedGame.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                  </div>
                )}
                <div className="p-6 border-b bg-gray-50/50">
                  <h2 className="text-3xl font-bold mb-2">
                    {selectedGame.title}
                  </h2>
                  <p className="text-gray-700">{selectedGame.description}</p>
                </div>
                <div className="p-6 grid gap-6">
                  {summary && (
                    <div className="bg-teal-50 border border-teal-100 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-teal-900 mb-2">
                        AI Summary
                      </h3>
                      <Markdown content={summary} />
                    </div>
                  )}
                  <div>
                    <div className="flex justify-between mb-4">
                      <h3 className="text-xl font-bold">Rules</h3>
                      {!summary && (
                        <button
                          onClick={handleSummarize}
                          disabled={loading}
                          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                        >
                          AI Summary
                        </button>
                      )}
                    </div>
                    <div className="bg-gray-50 rounded-xl p-6 border max-h-[500px] overflow-y-auto whitespace-pre-wrap text-gray-700">
                      {selectedGame.rules_content}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center text-gray-400 bg-white rounded-2xl border border-dashed">
                <svg
                  className="w-12 h-12 mb-4 text-gray-200"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.5"
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
                <p className="text-lg font-medium">Select a game</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
