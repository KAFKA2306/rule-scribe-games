import React, { useState, useEffect } from 'react';
import { Search, BookOpen, Plus, ArrowRight, Loader2, Save } from 'lucide-react';

// API Base URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [view, setView] = useState('home'); // home, search, create
  const [loading, setLoading] = useState(false);

  // Create/Edit State
  const [formData, setFormData] = useState({ term: '', definition: '', tags: '' });

  // Debounced search effect
  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (query.length > 1) {
        setLoading(true);
        try {
          const res = await fetch(`${API_URL}/search?q=${query}`);
          const data = await res.json();
          setResults(data);
          if (view === 'home') setView('search');
        } catch (e) {
          console.error(e);
          // Fallback for demo if API fails
          if (query.toLowerCase().includes('catan')) {
             setResults([{id: 1, term: 'Catan', definition: 'A multiplayer board game designed by Klaus Teuber.'}]);
          }
        }
        setLoading(false);
      } else if (query.length === 0) {
        setResults([]);
        if (view === 'search') setView('home');
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
        const payload = {
            term: formData.term,
            definition: formData.definition,
            tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean)
        };

        const res = await fetch(`${API_URL}/term`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            setView('search');
            setQuery(formData.term); // Trigger search for the new term
        }
    } catch (e) {
        alert("Failed to save");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900 font-sans selection:bg-indigo-100 selection:text-indigo-900">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-6 py-4 bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-neutral-200/50">
        <div className="flex items-center gap-2 cursor-pointer group" onClick={() => { setView('home'); setQuery(''); }}>
          <BookOpen className="w-6 h-6 text-indigo-600 transition-transform group-hover:scale-110" />
          <span className="font-bold text-xl tracking-tight">BoardGameDict</span>
        </div>
        <button
            onClick={() => { setView('create'); setFormData({term: query, definition: '', tags: ''}); }}
            className="flex items-center gap-2 text-sm font-medium bg-neutral-900 text-white px-4 py-2 rounded-full hover:bg-neutral-800 transition shadow-lg shadow-neutral-200">
            <Plus className="w-4 h-4" /> Contribute
        </button>
      </nav>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 pt-12 pb-24">

        {/* VIEW: HOME */}
        {view === 'home' && (
          <div className="flex flex-col items-center text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 mt-20">
            <h1 className="text-6xl font-extrabold tracking-tight text-neutral-900">
              Rule<span className="text-indigo-600">Scribe</span>
            </h1>
            <p className="text-xl text-neutral-500 max-w-lg leading-relaxed">
              The minimalist, community-powered encyclopedia for board game rules.
            </p>

            <div className="w-full max-w-xl relative group">
              <input
                type="text"
                className="w-full pl-14 pr-4 py-5 rounded-2xl border-2 border-transparent bg-white shadow-[0_8px_30px_rgb(0,0,0,0.04)] focus:shadow-[0_8px_30px_rgb(0,0,0,0.08)] focus:border-indigo-100 outline-none text-xl transition-all placeholder:text-neutral-300"
                placeholder="Search definitions..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                autoFocus
              />
              <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-neutral-400 w-6 h-6 group-focus-within:text-indigo-500 transition-colors" />
            </div>

            <div className="flex flex-wrap justify-center gap-3 text-sm text-neutral-400 pt-4">
              <span>Trending:</span>
              {['Catan', 'Wingspan', 'Azul', 'Dune: Imperium'].map(t => (
                  <button key={t} onClick={() => setQuery(t)} className="hover:text-indigo-600 hover:underline underline-offset-4 transition">{t}</button>
              ))}
            </div>
          </div>
        )}

        {/* VIEW: SEARCH RESULTS */}
        {view === 'search' && (
           <div className="space-y-8 animate-in fade-in duration-500">
             {/* Search Header */}
             <div className="sticky top-20 z-40 bg-neutral-50/95 backdrop-blur py-4 -mx-4 px-4 border-b border-transparent transition-all" style={{ borderColor: query ? 'transparent' : ''}}>
                <div className="relative max-w-2xl">
                  <input
                    type="text"
                    className="w-full pl-12 pr-4 py-3 rounded-xl border border-neutral-200 bg-white focus:ring-2 focus:ring-indigo-100 focus:border-indigo-500 outline-none transition-shadow shadow-sm"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-400 w-5 h-5" />
                  {loading && <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 text-indigo-500 w-5 h-5 animate-spin" />}
                </div>
             </div>

             <div className="grid gap-6 max-w-2xl">
               {results.map((r) => (
                 <article key={r.id} className="group p-6 bg-white rounded-2xl border border-neutral-100 shadow-[0_2px_8px_rgb(0,0,0,0.02)] hover:shadow-[0_8px_24px_rgb(0,0,0,0.06)] transition-all duration-300 cursor-pointer">
                   <div className="flex justify-between items-start">
                     <h3 className="text-2xl font-bold text-neutral-900 mb-2 group-hover:text-indigo-600 transition-colors">{r.term}</h3>
                     {r.popularity > 10 && <span className="text-xs font-semibold bg-indigo-50 text-indigo-600 px-2 py-1 rounded-md">Popular</span>}
                   </div>
                   <p className="text-neutral-600 leading-relaxed text-lg">{r.definition}</p>
                   {r.tags && (
                       <div className="flex gap-2 mt-4">
                           {r.tags.map(tag => (
                               <span key={tag} className="text-xs font-medium text-neutral-400 bg-neutral-100 px-2 py-1 rounded-full">#{tag}</span>
                           ))}
                       </div>
                   )}
                 </article>
               ))}

               {!loading && results.length === 0 && (
                 <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-neutral-300">
                   <p className="text-neutral-500 text-lg">No definition found for "{query}".</p>
                   <button
                    onClick={() => { setView('create'); setFormData({term: query, definition: '', tags: ''}); }}
                    className="mt-6 inline-flex items-center gap-2 text-indigo-600 font-semibold hover:text-indigo-700 hover:underline underline-offset-4 transition">
                    <Plus className="w-5 h-5" /> Add definition to dictionary
                   </button>
                 </div>
               )}
             </div>
           </div>
        )}

        {/* VIEW: CREATE/EDIT */}
        {view === 'create' && (
            <div className="max-w-xl mx-auto animate-in zoom-in-95 duration-300">
                <div className="mb-6">
                    <button onClick={() => setView('search')} className="text-sm text-neutral-500 hover:text-neutral-900 transition mb-4">&larr; Back to search</button>
                    <h2 className="text-3xl font-bold">Contribute Knowledge</h2>
                    <p className="text-neutral-500">Help the community by adding a new term.</p>
                </div>

                <form onSubmit={handleCreate} className="space-y-6 bg-white p-8 rounded-3xl shadow-xl shadow-neutral-200/50 border border-neutral-100">
                    <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">Term / Game Name</label>
                        <input
                            required
                            className="w-full px-4 py-3 rounded-xl border border-neutral-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                            value={formData.term}
                            onChange={e => setFormData({...formData, term: e.target.value})}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">Definition / Rule Summary</label>
                        <textarea
                            required
                            rows={6}
                            className="w-full px-4 py-3 rounded-xl border border-neutral-200 focus:ring-2 focus:ring-indigo-500 outline-none resize-none"
                            placeholder="Explain the term or rule clearly..."
                            value={formData.definition}
                            onChange={e => setFormData({...formData, definition: e.target.value})}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-neutral-700 mb-1">Tags (comma separated)</label>
                        <input
                            className="w-full px-4 py-3 rounded-xl border border-neutral-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                            placeholder="e.g. strategy, worker-placement"
                            value={formData.tags}
                            onChange={e => setFormData({...formData, tags: e.target.value})}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full flex justify-center items-center gap-2 bg-indigo-600 text-white font-bold py-4 rounded-xl hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
                        {loading ? <Loader2 className="animate-spin" /> : <Save className="w-5 h-5" />}
                        Save Definition
                    </button>
                </form>
            </div>
        )}

      </main>
    </div>
  );
}

export default App;
