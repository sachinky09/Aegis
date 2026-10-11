export class ApiError extends Error {
  status: number
  body: string
  constructor(status: number, body: string) {
    super(`HTTP ${status}`)
    this.status = status
    this.body = body
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    })
  } catch (e: any) {
    throw new ApiError(0, e?.message || 'Network error')
  }
  const text = await res.text()
  let data: any = null
  try { data = text ? JSON.parse(text) : null } catch { data = text }
  if (!res.ok) throw new ApiError(res.status, typeof data === 'string' ? data : JSON.stringify(data))
  return data as T
}

export function unwrap<T = any>(res: any): T {
  if (res && typeof res === 'object' && 'data' in res && ('success' in res || 'timestamp' in res)) return res.data as T
  return res as T
}

const get = <T>(p: string) => request<T>(p)
const post = <T>(p: string, body?: unknown) => request<T>(p, { method: 'POST', body: body != null ? JSON.stringify(body) : undefined })
const del = <T>(p: string) => request<T>(p, { method: 'DELETE' })

export const api = {
  healthBackend: () => get<any>('/actuator/health'),
  healthMl: () => get<any>('/health'),
  instruments: () => get<any>('/api/instruments').then(unwrap),
  watchlist: () => get<any>('/api/watchlist').then(unwrap),
  addToWatchlist: (body: { symbol: string; name?: string; sector?: string; lotSize?: number }) =>
    post<any>('/api/watchlist', body),
  removeFromWatchlist: (symbol: string) => del<any>(`/api/watchlist/${encodeURIComponent(symbol)}`),
  paperSummary: () => get<any>('/api/paper/summary').then(unwrap),
  paperOrders: () => get<any>('/api/paper/orders').then(unwrap),
  paperPositions: () => get<any>('/api/paper/positions').then(unwrap),
  placeOrder: (body: unknown) => post<any>('/api/paper/orders', body),
  signals: () => get<any>('/api/signals').then(unwrap),
  search: (q: string) => get<any>(`/market/search?q=${encodeURIComponent(q)}`),
  liveQuote: (symbol: string) => get<any>(`/market/live/${encodeURIComponent(symbol)}`),
  moveDiagnosis: (symbol: string) => get<any>(`/market/move-diagnosis/${encodeURIComponent(symbol)}`),
  features: (symbol: string) => get<any>(`/market/features/${encodeURIComponent(symbol)}`),
  analyzeNews: (body: { symbol: string; query?: string }) => post<any>('/news/analyze', body),
  predict: (body: unknown) => post<any>('/models/predict', body),
  automationStatus: () => get<any>('/automation/status'),
  newsStatus: () => get<any>('/news/status'),
  runBacktest: (body: unknown) => post<any>('/backtest/run', body),
  optionGreeks: (body: unknown) => post<any>('/options/greeks', body),
  optimizePortfolio: (body: unknown) => post<any>('/portfolio/optimize', body),
}
