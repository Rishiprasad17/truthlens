import React, { useState, useEffect } from 'react'
import { Card, SectionLabel, MetricCard, Btn } from '../components/UI'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts'

const PROXY_URL = 'http://localhost:8001'
const COLORS = { Low: '#1D9E75', Medium: '#EF9F27', High: '#E24B4A' }
const MODEL_COLORS = ['#1D9E75', '#6B7FD7', '#EF9F27', '#E24B4A', '#A855F7']

export default function ProxyPage() {
  const [analytics, setAnalytics] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('analytics')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true); setError(null)
    try {
      const [a, h] = await Promise.all([
        fetch(`${PROXY_URL}/analytics`).then(r => r.json()),
        fetch(`${PROXY_URL}/history?limit=50`).then(r => r.json()),
      ])
      setAnalytics(a)
      setHistory(h.evaluations || [])
    } catch (e) {
      setError('Proxy not running. Start it with: python -m truthlens.cli proxy')
    } finally { setLoading(false) }
  }

  async function exportCsv() {
    await fetch(`${PROXY_URL}/export`, { method: 'POST' })
    alert('Exported to truthlens_export.csv in your project folder')
  }

  const riskData = analytics ? [
    { name: 'Low',    value: analytics.low_risk_count    || 0 },
    { name: 'Medium', value: analytics.medium_risk_count || 0 },
    { name: 'High',   value: analytics.high_risk_count   || 0 },
  ].filter(d => d.value > 0) : []

  const trendData = analytics?.trend?.slice().reverse().map(t => ({
    date: t.date?.slice(5),
    trust: Math.round(t.avg_trust || 0),
    count: t.count,
  })) || []

  return (
    <div style={{ padding: '1.5rem', overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <SectionLabel>Proxy Analytics</SectionLabel>
        <div style={{ display: 'flex', gap: 8 }}>
          <Btn onClick={load} style={{ fontSize: 12 }}>↻ Refresh</Btn>
          <Btn onClick={exportCsv} style={{ fontSize: 12 }}>↓ Export CSV</Btn>
        </div>
      </div>

      {error && (
        <div style={{ background: 'rgba(226,75,74,0.08)', border: '1px solid rgba(226,75,74,0.3)', borderRadius: 8, padding: '12px 16px' }}>
          <div style={{ color: '#E24B4A', fontSize: 13, fontFamily: 'var(--font-mono)' }}>{error}</div>
          <div style={{ color: 'var(--muted)', fontSize: 11, marginTop: 6, fontFamily: 'var(--font-mono)' }}>
            Run in a new terminal: <span style={{ color: '#1D9E75' }}>python -m truthlens.cli proxy</span>
          </div>
        </div>
      )}

      {!error && analytics && (
        <>
          {analytics.total === 0 ? (
            <Card style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
              <div style={{ marginBottom: 8 }}>// no proxy calls logged yet</div>
              <div style={{ fontSize: 11 }}>Send requests to http://localhost:8001/chat to see data here</div>
            </Card>
          ) : (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
                <MetricCard label="Total Calls" value={analytics.total} color="var(--text)" />
                <MetricCard label="Avg Trust" value={`${analytics.avg_trust}`} />
                <MetricCard label="Avg Ground." value={`${analytics.avg_groundedness}%`} />
                <MetricCard label="High Risk" value={`${analytics.high_risk_count}`} color="#E24B4A" />
                <MetricCard label="Avg Latency" value={`${Math.round(analytics.avg_latency_ms)}ms`} color="var(--muted)" />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
                {trendData.length > 1 && (
                  <Card>
                    <SectionLabel>Trust Score Trend</SectionLabel>
                    <ResponsiveContainer width="100%" height={180}>
                      <LineChart data={trendData}>
                        <XAxis dataKey="date" tick={{ fill: '#888884', fontSize: 11 }} axisLine={false} tickLine={false} />
                        <YAxis domain={[0, 100]} tick={{ fill: '#888884', fontSize: 11 }} axisLine={false} tickLine={false} />
                        <Tooltip contentStyle={{ background: '#111', border: '1px solid #222', borderRadius: 6, fontFamily: 'DM Mono', fontSize: 12 }} />
                        <Line dataKey="trust" stroke="#1D9E75" strokeWidth={2} dot={false} name="Avg Trust" />
                      </LineChart>
                    </ResponsiveContainer>
                  </Card>
                )}

                {riskData.length > 0 && (
                  <Card>
                    <SectionLabel>Hallucination Risk</SectionLabel>
                    <ResponsiveContainer width="100%" height={180}>
                      <PieChart>
                        <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={65}
                          label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                          {riskData.map((e, i) => <Cell key={i} fill={COLORS[e.name]} />)}
                        </Pie>
                        <Tooltip contentStyle={{ background: '#111', border: '1px solid #222', borderRadius: 6, fontFamily: 'DM Mono', fontSize: 12 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </Card>
                )}
              </div>

              {analytics.by_model?.length > 0 && (
                <Card>
                  <SectionLabel>Performance by Model</SectionLabel>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                    <thead>
                      <tr>
                        {['Model', 'Provider', 'Calls', 'Avg Trust', 'Avg Ground.', 'Avg Faith.', 'High Risk'].map(h => (
                          <th key={h} style={{ textAlign: 'left', padding: '6px 10px', fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', borderBottom: '1px solid var(--border)', fontWeight: 500 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {analytics.by_model.map((m, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                          <td style={{ padding: '8px 10px', fontWeight: 600, fontFamily: 'var(--font-mono)', fontSize: 12 }}>{m.model}</td>
                          <td style={{ padding: '8px 10px', color: 'var(--muted)', fontSize: 12 }}>{m.provider}</td>
                          <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>{m.count}</td>
                          <td style={{ padding: '8px 10px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#1D9E75' }}>{m.avg_trust?.toFixed(1)}</td>
                          <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: 'var(--muted)', fontSize: 12 }}>{m.avg_groundedness?.toFixed(1)}%</td>
                          <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: 'var(--muted)', fontSize: 12 }}>{m.avg_faithfulness?.toFixed(1)}%</td>
                          <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: m.high_risk_count > 0 ? '#E24B4A' : 'var(--muted)', fontSize: 12 }}>{m.high_risk_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Card>
              )}
            </>
          )}
        </>
      )}

      {history.length > 0 && (
        <Card>
          <SectionLabel>Recent Calls ({history.length})</SectionLabel>
          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {history.map((h, i) => (
              <div key={i} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, color: 'var(--text)', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {h.prompt}
                  </div>
                  <div style={{ display: 'flex', gap: 10, fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--muted)' }}>
                    <span style={{ color: '#6B7FD7' }}>{h.provider}</span>
                    <span>{h.model}</span>
                    <span style={{ color: h.hallucination_risk === 'Low' ? '#1D9E75' : h.hallucination_risk === 'High' ? '#E24B4A' : '#EF9F27' }}>
                      {h.hallucination_risk}
                    </span>
                    <span>{h.timestamp?.slice(0, 16).replace('T', ' ')}</span>
                  </div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontSize: 18, fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#1D9E75', lineHeight: 1 }}>{Math.round(h.trust_score)}</div>
                  <div style={{ fontSize: 10, color: 'var(--muted)' }}>/ 100</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <SectionLabel>Integration — 2 lines of code</SectionLabel>
        <pre style={{ fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.8, color: 'var(--text)', background: 'var(--surface2)', borderRadius: 6, padding: '1rem', overflowX: 'auto' }}>
{`from proxy.sdk import TruthLens

# OpenAI
tl = TruthLens(provider="openai", model="gpt-4o", api_key="sk-...")
response = tl.chat("Who created Python?", sources=["Python was created by Guido..."])
print(response.trust_score)      # 95.0
print(response.hallucination_risk)  # Low

# Ollama (no API key needed)
tl = TruthLens(provider="ollama", model="llama3")
response = tl.chat("Explain quantum computing")
print(response.summary())
# [TruthLens] Trust: 87/100 | Ground: 91% | Faith: 88% | Hallucination: ✓ Low`}
        </pre>
      </Card>
    </div>
  )
}
