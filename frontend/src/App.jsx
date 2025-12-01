import React, { useState } from 'react';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedGame, setSelectedGame] = useState(null);
  const [summary, setSummary] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults([]);
    setSelectedGame(null);
    setSummary(null);

    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectGame = (game) => {
    setSelectedGame(game);
    setSummary(null);
  };

  const handleSummarize = async () => {
    if (!selectedGame) return;
    setLoading(true);
    try {
        const response = await fetch('/api/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: selectedGame.rules_content }),
        });
        const data = await response.json();
        setSummary(data.summary);
    } catch (error) {
        console.error('Summarize failed:', error);
    } finally {
        setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>RuleScribe Minimal</h1>
      <form onSubmit={handleSearch} style={{ marginBottom: '2rem' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for a game (e.g., Catan)..."
          style={{ padding: '0.5rem', width: '70%', marginRight: '0.5rem' }}
        />
        <button type="submit" style={{ padding: '0.5rem 1rem' }} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      <div style={{ display: 'flex', gap: '2rem' }}>
        <div style={{ flex: 1 }}>
            <h2>Results</h2>
            {results.length === 0 && <p>No results found.</p>}
            <ul style={{ listStyle: 'none', padding: 0 }}>
                {results.map((game) => (
                <li
                    key={game.id}
                    onClick={() => handleSelectGame(game)}
                    style={{
                    padding: '1rem',
                    border: '1px solid #ddd',
                    marginBottom: '0.5rem',
                    cursor: 'pointer',
                    background: selectedGame?.id === game.id ? '#f0f0f0' : 'white'
                    }}
                >
                    <strong>{game.title}</strong>
                    <p style={{ margin: '0.5rem 0 0', fontSize: '0.9rem', color: '#666' }}>{game.description}</p>
                </li>
                ))}
            </ul>
        </div>

        {selectedGame && (
            <div style={{ flex: 1, borderLeft: '1px solid #eee', paddingLeft: '2rem' }}>
                <h2>{selectedGame.title}</h2>
                <p>{selectedGame.description}</p>
                <div style={{ marginTop: '1rem', padding: '1rem', background: '#f9f9f9' }}>
                    <h3>Rules Content</h3>
                    <p style={{ whiteSpace: 'pre-wrap', maxHeight: '200px', overflowY: 'auto' }}>
                        {selectedGame.rules_content}
                    </p>
                </div>
                <button
                    onClick={handleSummarize}
                    style={{ marginTop: '1rem', padding: '0.5rem 1rem', background: '#0070f3', color: 'white', border: 'none', cursor: 'pointer' }}
                    disabled={loading}
                >
                    {loading ? 'Summarizing...' : 'Summarize Rules'}
                </button>
                {summary && (
                    <div style={{ marginTop: '1rem', padding: '1rem', background: '#e6fffa', border: '1px solid #b2f5ea' }}>
                        <h3>AI Summary</h3>
                        <p>{summary}</p>
                    </div>
                )}
            </div>
        )}
      </div>
    </div>
  );
}

export default App;
