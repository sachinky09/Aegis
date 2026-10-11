import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'

const INDICES = ['^NSEI', '^BSESN']
const TOP20 = [
  'RELIANCE','TCS','HDFCBANK','BHARTIARTL','ICICIBANK','INFY','SBIN','HINDUNILVR',
  'ITC','LT','KOTAKBANK','AXISBANK','BAJFINANCE','ASIANPAINT','MARUTI','SUNPHARMA',
  'TITAN','WIPRO','ULTRACEMCO','NESTLEIND',
]

export default function Dashboard() {
  const [rows, setRows] = useState<any[]>([])
  const [idx, setIdx] = useState<any[]>([])
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setErr('')
    try {
      const indexQuotes = await Promise.all(INDICES.map(s => api.liveQuote(s).catch(e => ({ ok: false, symbol: s, error: String(e) }))))
      const topQuotes = await Promise.all(TOP20.map(s => api.liveQuote(s).catch(e => ({ ok: false, symbol: s, error: String(e) }))))
      setIdx(indexQuotes)
      setRows(topQuotes)
    } catch (e: any) {
      setErr(e?.message || 'Failed to load market pulse')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 60000)
    return () => clearInterval(t)
  }, [])

  return (
    <div>
      <h1 className="page-title">Market pulse</h1>
      <p className="page-sub">Default live stream: NSE/BSE indices + top liquid names. Your watchlist is separate and starts empty.</p>
      {err && <p className="err">{err}</p>}
      {loading && <p className="muted">Loading live quotes…</p>}

      <div className="grid grid-2" style={{ marginBottom: '1rem' }}>
        {idx.map((q) => (
          <div className="card" key={q.symbol || q.attempts}>
            <div className="stat-label">{q.symbol === '^NSEI' ? 'Nifty 50' : q.symbol === '^BSESN' ? 'Sensex' : q.symbol}</div>
            {q.ok ? (
              <>
                <div className="stat-value">₹{Number(q.last).toLocaleString('en-IN')}</div>
                <div className={q.change_pct >= 0 ? 'ok' : 'err'}>{Number(q.change_pct).toFixed(2)}% · {q.source}</div>
              </>
            ) : (
              <div className="err">Unavailable · {q.error || JSON.stringify(q.attempts)}</div>
            )}
          </div>
        ))}
      </div>

      <div className="card">
        <h2>Top liquid (live stream defaults)</h2>
        <table>
          <thead>
            <tr><th>#</th><th>Symbol</th><th>LTP</th><th>Chg %</th><th>Source</th><th></th></tr>
          </thead>
          <tbody>
            {rows.map((q, i) => (
              <tr key={q.symbol || i}>
                <td>{i + 1}</td>
                <td><strong>{q.symbol}</strong></td>
                <td>{q.ok ? Number(q.last).toFixed(2) : '—'}</td>
                <td className={q.ok && q.change_pct >= 0 ? 'ok' : q.ok ? 'err' : 'muted'}>
                  {q.ok ? `${Number(q.change_pct).toFixed(2)}%` : (q.error || 'error')}
                </td>
                <td>{q.source || '—'}</td>
                <td><Link to={`/symbol/${q.symbol}`}>Open</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
