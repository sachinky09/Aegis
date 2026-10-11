import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api'

export default function SymbolPage() {
  const { symbol = '' } = useParams()
  const sym = symbol.toUpperCase()
  const [quote, setQuote] = useState<any>(null)
  const [diag, setDiag] = useState<any>(null)
  const [pred, setPred] = useState<any>(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState('')
  const [qty, setQty] = useState(1)
  const [side, setSide] = useState('BUY')
  const [tradeMsg, setTradeMsg] = useState('')

  const load = async () => {
    setErr('')
    try {
      const q = await api.liveQuote(sym)
      setQuote(q)
      if (!q.ok) setErr(q.error || 'Live quote failed')
    } catch (e: any) {
      setErr(e?.body || e?.message || 'Quote error')
      setQuote(null)
    }
  }

  useEffect(() => { load(); const t = setInterval(load, 60000); return () => clearInterval(t) }, [sym])

  const runDiag = async () => {
    setBusy('diag')
    try { setDiag(await api.moveDiagnosis(sym)) }
    catch (e: any) { setDiag({ ok: false, error: e?.body || e?.message }) }
    setBusy('')
  }

  const runPred = async () => {
    setBusy('pred')
    try {
      setPred(await api.predict({ symbol: sym, features: [0.1, 0.05, -0.02, 0.03, 0.01, 0, 0.02, -0.01] }))
    } catch (e: any) {
      setPred({ error: e?.body || e?.message })
    }
    setBusy('')
  }

  const trade = async () => {
    setTradeMsg('')
    if (!quote?.ok) { setTradeMsg('Cannot trade without a live price'); return }
    try {
      const r = await api.placeOrder({
        symbol: sym, side, orderType: 'MARKET', quantity: Number(qty), marketPrice: quote.last,
      })
      setTradeMsg(r.message || JSON.stringify(r))
    } catch (e: any) {
      setTradeMsg(e?.body || e?.message || 'Order failed')
    }
  }

  const addWl = async () => {
    try { await api.addToWatchlist({ symbol: sym, name: quote?.company }); setTradeMsg('Added to watchlist') }
    catch (e: any) { setTradeMsg(e?.body || e?.message) }
  }
  const rmWl = async () => {
    try { await api.removeFromWatchlist(sym); setTradeMsg('Removed from watchlist') }
    catch (e: any) { setTradeMsg(e?.body || e?.message) }
  }

  return (
    <div>
      <h1 className="page-title">{sym}</h1>
      <p className="page-sub">{quote?.company || 'Symbol workspace'} · live + diagnosis + ML + paper</p>
      {err && <p className="err">{err}</p>}
      {tradeMsg && <p className="muted">{tradeMsg}</p>}

      <div className="grid grid-3" style={{ marginBottom: '1rem' }}>
        <div className="card">
          <div className="stat-label">Live quote</div>
          {quote?.ok ? (
            <>
              <div className="stat-value">₹{Number(quote.last).toLocaleString('en-IN')}</div>
              <div className={quote.change_pct >= 0 ? 'ok' : 'err'}>{Number(quote.change_pct).toFixed(2)}% · {quote.source}</div>
              <div className="muted" style={{ fontSize: 12 }}>{quote.as_of}</div>
            </>
          ) : (
            <div className="err">No live price{quote?.attempts ? `: ${JSON.stringify(quote.attempts)}` : ''}</div>
          )}
          <div className="row" style={{ marginTop: 10 }}>
            <button type="button" className="secondary" onClick={load}>Refresh</button>
            <button type="button" className="secondary" onClick={addWl}>Add watchlist</button>
            <button type="button" className="danger" onClick={rmWl}>Remove</button>
          </div>
        </div>

        <div className="card">
          <h2>ML prediction</h2>
          <button type="button" disabled={busy === 'pred'} onClick={runPred}>{busy === 'pred' ? '…' : 'Run predict'}</button>
          {pred && !pred.error && (
            <div style={{ marginTop: 8 }}>
              <div className="stat-value">{pred.prediction}</div>
              <div className="muted">score {pred.score?.toFixed?.(3)} · {pred.model}</div>
            </div>
          )}
          {pred?.error && <p className="err">{pred.error}</p>}
        </div>

        <div className="card">
          <h2>Paper trade (unlimited cash)</h2>
          <div className="row">
            <select value={side} onChange={e => setSide(e.target.value)} style={{ width: 100 }}>
              <option>BUY</option><option>SELL</option>
            </select>
            <input type="number" min={1} value={qty} onChange={e => setQty(Number(e.target.value))} style={{ width: 100 }} />
            <button type="button" onClick={trade}>Submit</button>
          </div>
          <p className="muted" style={{ marginTop: 8, fontSize: 12 }}>Uses live LTP when available. Lot rules still apply when instrument has lot size.</p>
        </div>
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <h2>Why is it moving (4 layers)</h2>
          <button type="button" disabled={busy === 'diag'} onClick={runDiag}>{busy === 'diag' ? '…' : 'Run diagnosis'}</button>
        </div>
        {diag?.ok === false && <p className="err">{diag.error}</p>}
        {diag?.summary && <p style={{ lineHeight: 1.5 }}>{diag.summary}</p>}
        {diag?.layers && (
          <div className="grid grid-2" style={{ marginTop: 12 }}>
            <div>
              <div className="stat-label">Drivers</div>
              {(diag.drivers || []).map((d: any) => (
                <div key={d.type} style={{ marginBottom: 8 }}>
                  <div className="row" style={{ justifyContent: 'space-between' }}>
                    <span>{d.type}</span><span>{d.score}</span>
                  </div>
                  <div className="driver-bar"><span style={{ width: `${Math.min(100, d.score * 100)}%` }} /></div>
                  <div className="muted" style={{ fontSize: 12 }}>{d.evidence}</div>
                </div>
              ))}
            </div>
            <div>
              <div className="stat-label">Headlines</div>
              {(diag.headlines || []).length === 0 && <div className="muted">None</div>}
              {(diag.headlines || []).slice(0, 6).map((h: any, i: number) => (
                <div className="headline" key={i}>{h.title}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
