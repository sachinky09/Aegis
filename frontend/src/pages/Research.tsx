import { useState } from 'react'
import { api } from '../services/api'

export default function Research() {
  const [symbol, setSymbol] = useState('RELIANCE')
  const [out, setOut] = useState<any>(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState('')

  const run = async (fn: () => Promise<any>, key: string) => {
    setBusy(key); setErr(''); setOut(null)
    try { setOut(await fn()) }
    catch (e: any) { setErr(e?.body || e?.message || 'Failed') }
    setBusy('')
  }

  return (
    <div>
      <h1 className="page-title">Research</h1>
      <p className="page-sub">Backtest / options / portfolio — requires real data where applicable.</p>
      <div className="card" style={{ maxWidth: 400, marginBottom: 12 }}>
        <input value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())} />
      </div>
      <div className="row" style={{ marginBottom: 12 }}>
        <button disabled={!!busy} onClick={() => run(() => api.runBacktest({ symbol, n_samples: 120, n_splits: 4 }), 'bt')}>Backtest</button>
        <button className="secondary" disabled={!!busy} onClick={() => run(() => api.optionGreeks({ spot: 2800, strike: 2800, time_to_expiry_years: 0.08, iv: 0.22 }), 'og')}>Greeks</button>
        <button className="secondary" disabled={!!busy} onClick={() => run(() => api.optimizePortfolio({ symbols: [symbol, 'TCS'], expected_returns: [0.12, 0.1] }), 'pf')}>Portfolio</button>
      </div>
      {err && <p className="err">{err}</p>}
      {out && <pre className="card mono">{JSON.stringify(out, null, 2)}</pre>}
    </div>
  )
}
