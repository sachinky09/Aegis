import { NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { useCallback, useEffect, useState } from 'react'
import { api } from './services/api'
import Dashboard from './pages/Dashboard'
import Watchlist from './pages/Watchlist'
import PaperTrading from './pages/PaperTrading'
import SymbolPage from './pages/SymbolPage'
import Research from './pages/Research'
import SystemPage from './pages/SystemPage'

export default function App() {
  const [q, setQ] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  const [searchErr, setSearchErr] = useState('')
  const [pick, setPick] = useState<any>(null)
  const [feed, setFeed] = useState('…')
  const nav = useNavigate()

  useEffect(() => {
    Promise.all([api.healthBackend(), api.healthMl()])
      .then(() => setFeed('Services up'))
      .catch(() => setFeed('Service issue'))
  }, [])

  useEffect(() => {
    if (q.trim().length < 2) { setResults([]); setSearchErr(''); return }
    const t = setTimeout(async () => {
      setSearching(true); setSearchErr('')
      try {
        const r = await api.search(q.trim())
        setResults((r.results || []).filter((x: any) => x.symbol))
        if (r.error) setSearchErr(r.error)
      } catch (e: any) {
        setSearchErr(e?.body || e?.message || 'Search failed')
        setResults([])
      } finally { setSearching(false) }
    }, 300)
    return () => clearTimeout(t)
  }, [q])

  const addWatch = useCallback(async (row: any) => {
    try {
      await api.addToWatchlist({ symbol: row.symbol, name: row.name, lotSize: 1 })
      setPick(null); setQ(''); setResults([])
      nav('/watchlist')
    } catch (e: any) {
      alert(e?.body || e?.message || 'Add failed')
    }
  }, [nav])

  return (
    <div className="shell">
      <aside className="nav">
        <h1>AEGIS</h1>
        <div className="tag">Live NSE / BSE lab</div>
        <NavLink to="/" end>Market pulse</NavLink>
        <NavLink to="/watchlist">My watchlist</NavLink>
        <NavLink to="/paper">Paper trading</NavLink>
        <NavLink to="/research">Research</NavLink>
        <NavLink to="/system">System</NavLink>
        <div style={{ marginTop: 'auto', paddingTop: '2rem' }} className="muted" >{feed}</div>
      </aside>
      <div className="main">
        <div className="card" style={{ marginBottom: '1rem', position: 'relative' }}>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <input
              style={{ maxWidth: 420 }}
              placeholder="Search any Indian stock (e.g. IndusInd)"
              value={q}
              onChange={e => setQ(e.target.value)}
            />
            {searching && <span className="badge">Searching…</span>}
          </div>
          {searchErr && <p className="err" style={{ marginTop: 8 }}>{searchErr}</p>}
          {results.length > 0 && (
            <div style={{ marginTop: 8, maxHeight: 240, overflow: 'auto' }}>
              {results.map((r) => (
                <div key={r.yahoo_symbol || r.symbol} className="headline row" style={{ justifyContent: 'space-between' }}>
                  <div>
                    <strong>{r.symbol}</strong> <span className="muted">{r.name}</span>
                    <div className="badge">{r.exchange}</div>
                  </div>
                  <div className="row">
                    <button type="button" className="secondary" onClick={() => setPick(r)}>Choose</button>
                  </div>
                </div>
              ))}
            </div>
          )}
          {pick && (
            <div className="card" style={{ marginTop: 12, borderColor: 'var(--accent)' }}>
              <strong>{pick.symbol}</strong> — {pick.name}
              <div className="row" style={{ marginTop: 10 }}>
                <button type="button" onClick={() => addWatch(pick)}>Add to watchlist</button>
                <button type="button" className="secondary" onClick={() => { nav(`/symbol/${pick.symbol}`); setPick(null); setQ(''); setResults([]) }}>Open now</button>
                <button type="button" className="secondary" onClick={() => setPick(null)}>Cancel</button>
              </div>
            </div>
          )}
        </div>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/paper" element={<PaperTrading />} />
          <Route path="/symbol/:symbol" element={<SymbolPage />} />
          <Route path="/research" element={<Research />} />
          <Route path="/system" element={<SystemPage />} />
        </Routes>
      </div>
    </div>
  )
}
