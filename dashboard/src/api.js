const BASE = '/api'

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}

export const api = {
  health: () => get('/health'),
  models: () => get('/models'),
  evaluate: (body) => post('/evaluate', body),
  evaluateRag: (body) => post('/evaluate/rag', body),
  evaluateAgent: (body) => post('/evaluate/agent', body),
  compare: (body) => post('/compare', body),
}
