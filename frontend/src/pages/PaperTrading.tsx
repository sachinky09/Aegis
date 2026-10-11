import { useEffect, useState } from 'react'
import { api } from '../services/api'

export default function PaperTrading() {
  const [summary, setSummary] = useState<any>(null)
  const [orders, setOrders] = useState<any[]>([])
  const [err, setErr] = useState('')

  const load = async () => {
    try {
      setSummary(await api.paperSummary())
      const o = await api.paperOrders()
      setOrders(Array.isArray(o) ? o : [])
      setErr('')
    } catch (e: any) {
      setErr(e?.body || e?.message || 'Paper load failed')
    }
  }
  useEffect(() => { load() }, [])

  return (
    <div>
      <h1 className="page-title">Paper trading</h1>
      <p className="page-sub">Unlimited sim capital. Place trades from a symbol page. Positions and fills below.</p>
      {err && <p className="err">{err}</p>}
      <div className="grid grid-3" style={{ marginBottom: '1rem' }}>
        <div className="card">
          <div className="stat-label">Cash (sim)</div>
          <div className="stat-value">Unlimited</div>
          <div className="muted" style={{ fontSize: 12 }}>Ledger may show a large balance marker</div>
        </div>
        <div className="card">
          <div className="stat-label">Positions</div>
          <div className="stat-value">{summary?.positionCount ?? summary?.positions?.length ?? '—'}</div>
        </div>
        <div className="card">
          <div className="stat-label">Open symbols</div>
          <div className="muted">{(summary?.positions || []).map((p: any) => p.symbol).join(', ') || 'None'}</div>
        </div>
      </div>
      <div className="card">
        <h2>Positions</h2>
        <table>
          <thead><tr><th>Symbol</th><th>Qty</th><th>Avg cost</th></tr></thead>
          <tbody>
            {(summary?.positions || []).map((p: any) => (
              <tr key={p.symbol}><td>{p.symbol}</td><td>{p.quantity}</td><td>{p.avgCost}</td></tr>
            ))}
          </tbody>
        </table>
        {(summary?.positions || []).length === 0 && <div className="empty">No positions</div>}
      </div>
      <div className="card" style={{ marginTop: '1rem' }}>
        <h2>Recent orders</h2>
        <table>
          <thead><tr><th>Symbol</th><th>Side</th><th>Qty</th><th>Price</th><th>Status</th></tr></thead>
          <tbody>
            {orders.slice(0, 20).map((o: any) => (
              <tr key={o.id}><td>{o.symbol}</td><td>{o.side}</td><td>{o.quantity}</td><td>{o.avgFillPrice}</td><td>{o.status}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <button type="button" className="secondary" style={{ marginTop: 12 }} onClick={load}>Refresh</button>
    </div>
  )
}
