import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedGame, setSelectedGame] = useState(null)
  const [summary, setSummary] = useState(null)

  const api = async (url, body) => {
    try {
      setLoading(true)
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error('Request failed')
      return await res.json()
    } catch (err) {
      console.error(err)
      return null
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setResults([])
    setSelectedGame(null)
    setSummary(null)
    setError(null)

    const data = await api('/api/search', { query })
    if (data) {
      setResults(data)
    } else {
      setError(
        'Search failed. Please check the backend connection or API keys.',
      )
    }
  }

  const handleSummarize = async () => {
    if (!selectedGame) return
    setError(null)
    const data = await api('/api/summarize', {
      text: selectedGame.rules_content,
    })
    if (data) {
      setSummary(data.summary)
    } else {
      setError('Summarization failed.')
    }
  }

  const clearSearch = () => {
    setQuery('')
    setResults([])
    setSelectedGame(null)
    setSummary(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-indigo-100 selection:text-indigo-900 flex flex-col">
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/70 border-b border-slate-200/50 supports-[backdrop-filter]:bg-white/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3 cursor-pointer" onClick={clearSearch}>
              <div className="bg-indigo-600 text-white p-1.5 rounded-lg">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600">
                RuleScribe
              </span>
            </div>
            <nav className="flex gap-4">
             <a href="#" className="text-sm font-medium text-slate-600 hover:text-indigo-600 transition-colors">About</a>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-grow">
        <div className="relative overflow-hidden bg-slate-50 pt-16 pb-24 lg:pt-20 lg:pb-32">
          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center z-10">
             <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 mb-6">
              The Living <span className="text-indigo-600">Grimoire</span>
            </h1>
            <p className="mt-4 max-w-2xl mx-auto text-xl text-slate-600 mb-10">
              Master any game instantly. AI-powered rule synthesis that evolves with every search.
            </p>

            <div className="max-w-2xl mx-auto relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-violet-500 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
              <form onSubmit={handleSearch} className="relative">
                <input
                  type="text"
                  className="block w-full pl-5 pr-32 py-5 border-0 rounded-xl text-lg bg-white shadow-xl ring-1 ring-slate-900/5 placeholder:text-slate-400 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all"
                  placeholder="Search a game (e.g. 'Catan' or URL)..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <div className="absolute inset-y-2 right-2 flex gap-2">
                    {query && (
                        <button
                            type="button"
                            onClick={() => setQuery('')}
                            className="p-2 text-slate-400 hover:text-slate-600 transition-colors"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                        </button>
                    )}
                    <button
                    type="submit"
                    disabled={loading}
                    className="px-6 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-sm transition-all hover:scale-105 active:scale-95 disabled:opacity-70 disabled:hover:scale-100"
                    >
                    {loading ? (
                        <span className="flex items-center gap-2">
                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                        Searching
                        </span>
                    ) : 'Search'}
                    </button>
                </div>
              </form>
            </div>
             {error && (
                <div className="mt-6 max-w-2xl mx-auto p-4 bg-red-50 text-red-700 border border-red-100 rounded-xl flex items-center gap-3 animate-fade-in">
                    <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  {error}
                </div>
              )}
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
            {/* Content Area */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Sidebar / List */}
            <div className={`lg:col-span-4 space-y-6 ${selectedGame ? 'hidden lg:block' : 'block'}`}>
              {results.length > 0 && (
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Found {results.length} Games</h2>
                  </div>
              )}
              
              <div className="space-y-4">
                {results.map((game) => (
                    <div
                    key={game.id}
                    onClick={() => {
                        setSelectedGame(game)
                        setSummary(null)
                        window.scrollTo({ top: document.getElementById('game-detail')?.offsetTop - 100, behavior: 'smooth' })
                    }}
                    className={`group relative bg-white rounded-2xl p-5 border transition-all duration-200 cursor-pointer hover:shadow-lg
                        ${selectedGame?.id === game.id 
                            ? 'border-indigo-500 ring-2 ring-indigo-100 shadow-md' 
                            : 'border-slate-200 hover:border-indigo-300'
                        }`}
                    >
                    <div className="flex gap-4">
                         {game.image_url ? (
                            <div className="h-16 w-16 rounded-lg bg-slate-100 flex-shrink-0 overflow-hidden">
                                <img src={game.image_url} alt="" className="h-full w-full object-cover" />
                            </div>
                         ) : (
                            <div className="h-16 w-16 rounded-lg bg-indigo-50 flex-shrink-0 flex items-center justify-center text-indigo-300">
                                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" /></svg>
                            </div>
                         )}
                         <div>
                             <h3 className={`font-bold text-lg group-hover:text-indigo-600 transition-colors ${selectedGame?.id === game.id ? 'text-indigo-700' : 'text-slate-800'}`}>
                                 {game.title}
                             </h3>
                             <p className="text-sm text-slate-500 line-clamp-2 mt-1">
                                 {game.description || "No description available."}
                             </p>
                         </div>
                    </div>
                    </div>
                ))}
                
                {results.length === 0 && !loading && query && !error && (
                   <div className="text-center py-12 px-4 rounded-3xl border-2 border-dashed border-slate-200 bg-slate-50">
                       <p className="text-slate-500">No games found in the database for "{query}".<br/>Trying to fetch from the web...</p>
                   </div>
                )}
              </div>
            </div>

            {/* Detail View */}
            <div id="game-detail" className={`lg:col-span-8 ${!selectedGame ? 'hidden lg:block' : 'block'}`}>
              {selectedGame ? (
                <div className="bg-white rounded-3xl shadow-xl border border-slate-100 overflow-hidden animate-fade-in">
                  {/* Cover Image */}
                  <div className="h-64 sm:h-80 w-full bg-slate-900 relative group">
                    {selectedGame.image_url ? (
                        <img
                        src={selectedGame.image_url}
                        alt={selectedGame.title}
                        className="w-full h-full object-cover opacity-90"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-800 to-slate-900">
                            <span className="text-slate-600 font-bold text-4xl opacity-20">{selectedGame.title}</span>
                        </div>
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent" />
                    <div className="absolute bottom-0 left-0 p-8">
                        <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight mb-2 shadow-black drop-shadow-lg">
                            {selectedGame.title}
                        </h1>
                         <button 
                            className="lg:hidden text-white/80 hover:text-white text-sm flex items-center gap-1 mt-2"
                            onClick={() => setSelectedGame(null)}
                        >
                             <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" /></svg>
                             Back to results
                        </button>
                    </div>
                  </div>

                  <div className="p-8">
                    {/* Actions */}
                    <div className="flex flex-wrap gap-4 mb-8 pb-8 border-b border-slate-100">
                         <button
                            onClick={handleSummarize}
                            disabled={loading || summary}
                            className={`flex items-center gap-2 px-5 py-2.5 rounded-full font-medium transition-all
                                ${summary 
                                    ? 'bg-teal-100 text-teal-700 cursor-default' 
                                    : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-200 hover:shadow-indigo-300'
                                }`}
                        >
                            {summary ? (
                                <>
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                                    Summarized
                                </>
                            ) : (
                                <>
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                                    Generate AI Summary
                                </>
                            )}
                        </button>
                        {selectedGame.source_url && (
                            <a 
                                href={selectedGame.source_url} 
                                target="_blank" 
                                rel="noreferrer"
                                className="flex items-center gap-2 px-5 py-2.5 rounded-full font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition-all"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                                Source
                            </a>
                        )}
                    </div>

                    {/* Summary Section */}
                    {summary && (
                        <div className="mb-8 bg-gradient-to-br from-teal-50 to-emerald-50 border border-teal-100 rounded-2xl p-6 shadow-sm">
                             <div className="flex items-center gap-2 mb-4 text-teal-800">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                                <h3 className="text-lg font-bold">Quick Summary</h3>
                             </div>
                            <ReactMarkdown className="prose prose-teal max-w-none">
                                {summary}
                            </ReactMarkdown>
                        </div>
                    )}

                    {/* Main Rules Content */}
                    <div className="prose prose-slate max-w-none prose-headings:text-indigo-900 prose-a:text-indigo-600 hover:prose-a:text-indigo-500">
                        <div className="flex items-center gap-2 mb-6 pb-2 border-b border-slate-100">
                             <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                             <h2 className="text-2xl font-bold text-slate-800 m-0">Full Rules</h2>
                        </div>
                        <div className="bg-slate-50 rounded-xl p-6 border border-slate-100">
                            <ReactMarkdown>{selectedGame.rules_content}</ReactMarkdown>
                        </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center p-12 text-center border-4 border-dashed border-slate-100 rounded-3xl bg-slate-50/50 min-h-[500px]">
                    <div className="bg-white p-4 rounded-full shadow-sm mb-4">
                        <svg
                            className="w-12 h-12 text-indigo-200"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="1.5"
                            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                            />
                        </svg>
                    </div>
                  <h3 className="text-xl font-bold text-slate-800 mb-2">Select a Game</h3>
                  <p className="text-slate-500 max-w-xs">Choose a game from the list or search for a new one to view its rules and get an AI summary.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
      
      <footer className="bg-white border-t border-slate-200 py-8 mt-auto">
          <div className="max-w-7xl mx-auto px-4 text-center text-slate-400 text-sm">
              <p>&copy; {new Date().getFullYear()} RuleScribe. Powered by Gemini & Supabase.</p>
          </div>
      </footer>
    </div>
  )
}

export default App