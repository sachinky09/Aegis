import { useEffect, useState } from 'react'
import { api } from '../services/api'

export default function SystemPage() {
  const [be, setBe] = useState<any>(null)
  const [ml, setMl] = useState<any>(null)
  const [auto, setAuto] = useState<any>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    (async () => {
      try {
        setBe(await api.healthBackend())
        setMl(await api.healthMl())
        try { setAuto(await api.automationStatus()) } catch { setAuto({ running: false }) }
      } catch (e: any) {
        setErr(e?.message || 'Health check failed')
      }
    })()
  }, [])

  return (
    <div>
      <h1 className="page-title">System</h1>
      <p className="page-sub">Health, automation (5 NSE-session retrains + 60s live poll). No Airflow.</p>
      {err && <p className="err">{err}</p>}
      <div className="grid grid-2">
        <div className="card">
          <h2>Backend</h2>
          <pre className="mono">{JSON.stringify(be, null, 2)}</pre>
        </div>
        <div className="card">
          <h2>ML</h2>
          <pre className="mono">{JSON.stringify(ml, null, 2)}</pre>
        </div>
        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <h2>Automation</h2>
          <pre className="mono">{JSON.stringify(auto, null, 2)}</pre>
        </div>
      </div>
    </div>
  )
}
