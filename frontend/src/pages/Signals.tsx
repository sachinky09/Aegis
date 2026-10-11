import { useEffect, useState } from 'react'
import { api } from '../services/api'

export default function Signals() {
  const [signals, setSignals] = useState<any[]>([])
  const [msg, setMsg] = useState('')

  const load = () => {
    api.signals().then(r => setSignals(r.data || [])).catch(e => setMsg(e.message))
  }

  useEffect(() => { load() }, [])

  const seed = async () => {
    try {
      await fetch('/api/signals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: 'RELIANCE',
          signalType: 'TECHNICAL',
          direction: 'LONG',
          strength: 0.72,
          metadata: JSON.stringify({ rsi: 32, note: 'oversold bounce' }),
        }),
      })
      load()
      setMsg('Demo signal created')
    } catch (e: any) {
      setMsg(e.message)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <h1>Signals</h1>
        <button onClick={seed}>Create Demo Signal</button>
      </div>
      {msg && <p style={{ color: 'var(--accent)', marginBottom: '1rem' }}>{msg}</p>}
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Type</th>
              <th>Direction</th>
              <th>Strength</th>
              <th>Status</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {signals.map((s: any) => (
              <tr key={s.id}>
                <td><strong>{s.symbol}</strong></td>
                <td>{s.signal_type}</td>
                <td>
                  <span className={`badge ${s.direction === 'LONG' || s.direction === 'UP' ? 'up' : 'down'}`}>
                    {s.direction}
                  </span>
                </td>
                <td>{s.strength}</td>
                <td>{s.status}</td>
                <td style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>{s.generated_at}</td>
              </tr>
            ))}
            {signals.length === 0 && (
              <tr><td colSpan={6} style={{ color: 'var(--muted)' }}>No signals yet — create a demo one</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
