import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'

export default function Watchlist() {
  const [items, setItems] = useState<any[]>([])
  const [quotes, setQuotes] = useState<Record<string, any>>({})
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')

  const refresh = useCallback(async () => {
    setErr('')
    try {
      const list = await api.watchlist()
      const arr = Array.isArray(list) ? list : []
      setItems(arr)
      const qmap: Record<string, any> = {}
      await Promise.all(arr.map(async (w: any) => {
        try { qmap[w.symbol] = await api.liveQuote(w.symbol) }
        catch (e: any) { qmap[w.symbol] = { ok: false, error: e?.message } }
      }))
      setQuotes(qmap)
    } catch (e: any) {
      setErr(e?.body || e?.message || 'Watchlist load failed')
    }
  }, [])

  useEffect(() => { refresh(); const t = setInterval(refresh, 60000); return () => clearInterval(t) }, [refresh])

  const remove = async (symbol: string) => {
    try {
      await api.removeFromWatchlist(symbol)
      setMsg(`Removed ${symbol}`)
      refresh()
    } catch (e: any) {
      setErr(e?.body || e?.message || 'Remove failed')
    }
  }

  return (
    <div>
      <h1 className="page-title">My watchlist</h1>
      <p className="page-sub">Personal list only. Search above to add any NSE/BSE name. Remove anytime.</p>
      {err && <p className="err">{err}</p>}
      {msg && <p className="ok">{msg}</p>}

      {items.length === 0 ? (
        <div className="card empty">No symbols yet. Use search to add IndusInd, Reliance, or any listed name.</div>
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr><th>Symbol</th><th>Name</th><th>LTP</th><th>Chg %</th><th>Source</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((w) => {
                const q = quotes[w.symbol] || {}
                return (
                  <tr key={w.symbol}>
                    <td><Link to={`/symbol/${w.symbol}`}><strong>{w.symbol}</strong></Link></td>
                    <td className="muted">{w.name || '—'}</td>
                    <td>{q.ok ? Number(q.last).toFixed(2) : '—'}</td>
                    <td className={q.ok && q.change_pct >= 0 ? 'ok' : 'err'}>{q.ok ? `${Number(q.change_pct).toFixed(2)}%` : (q.error || '—')}</td>
                    <td>{q.source || '—'}</td>
                    <td className="row">
                      <Link to={`/symbol/${w.symbol}`}>Open</Link>
                      <button type="button" className="danger" onClick={() => remove(w.symbol)}>Remove</button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
