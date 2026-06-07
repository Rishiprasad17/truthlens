import React, { useState, useRef, useEffect } from 'react'
import { Card, SectionLabel, Btn, Spinner, MetricCard } from '../components/UI'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts'

const COLORS = { Low: '#1D9E75', Medium: '#EF9F27', High: '#E24B4A' }

export default function BenchmarkPage() {
  const [mode, setMode] = useState('sample') // 'sample' | 'custom'
  const [casesJson, setCasesJson] = useState('')
  const [model, setModel] = useState('')
  const [includeClaims, setIncludeClaims] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [job, setJob] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const pollRef = useRef(null)

  useEffect(() => () => clearInterval(pollRef.current), [])

  async function start() {
    setLoading(true); setError(null); setJob(null)
    try {
      const body = {
        use_sample: mode === 'sample',
        cases: mode === 'custom' ? JSON.parse(casesJson) : undefined,
        model: model || undefined,
        include_claims: includeClaims,
      }
      const res = await fetch('/api/benchmark', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail) }
      const { job_id } = await res.json()
      setJobId(job_id)
      pollRef.current = setInterval(() => poll(job_id), 1500)
    } catch (e) { setError(e.message); setLoading(false) }
  }

  async function poll(id) {
    try {
      const res = await fetch(`/api/benchmark/${id}`)
      const data = await res.json()
      setJob(data)
      if (data.status === 'done' || data.status === 'error') {
        clearInterval(pollRef.current)
        setLoading(false)
      }
    } catch {}
  }

  const stats = job?.result?.stats
  const cases = job?.result?.cases || []

  const riskData = stats ? [
    { name: 'Low', value: stats.low_risk_count, pct: stats.low_risk_pct },
    { name: 'Medium', value: stats.medium_risk_count, pct: stats.medium_risk_pct },
    { name: 'High', value: stats.high_risk_count, pct: stats.high_risk_pct },
  ] : []

  const domainData = stats?.domain_stats
    ? Object.entries(stats.domain_stats).map(([domain, d]) => ({ domain, trust: d.avg_trust_score, ground: d.avg_groundedness }))
    : []

  const diffData = stats?.difficulty_stats
    ? Object.entries(stats.difficulty_stats).map(([diff, d]) => ({ difficulty: diff, trust: d.avg_trust_score }))
    : []

  return (
    <div style={{ padding: '1.5rem', overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <SectionLabel>Benchmark Runner — Phase 3</SectionLabel>

      <Card>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Dataset</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {['sample', 'custom'].map(m => (
                <button key={m} onClick={() => setMode(m)} style={{
                  padding: '7px 16px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                  background: mode === m ? '#1D9E75' : 'transparent',
                  color: mode === m ? '#fff' : 'var(--muted)',
                  border: `1px solid ${mode === m ? '#1D9E75' : 'var(--border)'}`,
                  cursor: 'pointer',
                }}>
                  {m === 'sample' ? 'Sample Dataset (5 cases)' : 'Custom JSON'}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Model</label>
            <input value={model} onChange={e => setModel(e.target.value)} placeholder="llama3 (default)" />
          </div>
        </div>

        {mode === 'custom' && (
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Cases JSON array</label>
            <textarea value={casesJson} onChange={e => setCasesJson(e.target.value)} rows={6}
              style={{ fontFamily: 'var(--font-mono)', fontSize: 12, resize: 'vertical' }}
              placeholder='[{"id":"1","question":"...","answer":"...","sources":["..."],"domain":"science","difficulty":"easy"}]' />
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--muted)', cursor: 'pointer' }}>
            <input type="checkbox" checked={includeClaims} onChange={e => setIncludeClaims(e.target.checked)} />
            Include claim-level verification (slower)
          </label>
          <Btn primary onClick={start} disabled={loading}>
            {loading ? <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Spinner /> Running…</span> : 'Run Benchmark →'}
          </Btn>
        </div>

        {loading && job && (
          <div style={{ marginTop: '1rem', background: 'var(--surface2)', borderRadius: 6, padding: '10px 14px' }}>
            <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--muted)', marginBottom: 6 }}>
              Progress: {job.progress} / {job.total}
            </div>
            <div style={{ height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ height: '100%', background: '#1D9E75', width: `${job.total ? (job.progress / job.total * 100) : 0}%`, transition: 'width 0.4s' }} />
            </div>
          </div>
        )}
        {error && <div style={{ marginTop: 10, color: '#E24B4A', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{error}</div>}
        {job?.status === 'error' && <div style={{ marginTop: 10, color: '#E24B4A', fontSize: 12, fontFamily: 'var(--font-mono)' }}>Error: {job.error}</div>}
      </Card>

      {stats && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
            <MetricCard label="Cases" value={stats.total_cases} />
            <MetricCard label="Avg Trust" value={`${stats.avg_trust_score}`} />
            <MetricCard label="Avg Ground." value={`${stats.avg_groundedness}%`} />
            <MetricCard label="Low Risk" value={`${stats.low_risk_pct}%`} />
            <MetricCard label="Avg Latency" value={`${Math.round(stats.avg_latency_ms)}ms`} color="var(--muted)" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            <Card>
              <SectionLabel>Hallucination Risk Distribution</SectionLabel>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={({ name, pct }) => `${name} ${pct}%`} labelLine={false}>
                    {riskData.map((entry, i) => <Cell key={i} fill={COLORS[entry.name]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#111', border: '1px solid #222', borderRadius: 6, fontFamily: 'DM Mono', fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            </Card>

            {domainData.length > 0 && (
              <Card>
                <SectionLabel>Trust Score by Domain</SectionLabel>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={domainData} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
                    <XAxis dataKey="domain" tick={{ fill: '#888884', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fill: '#888884', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ background: '#111', border: '1px solid #222', borderRadius: 6, fontFamily: 'DM Mono', fontSize: 12 }} />
                    <Bar dataKey="trust" name="Trust Score" fill="#1D9E75" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}
          </div>

          <Card>
            <SectionLabel>Case Results</SectionLabel>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr>
                    {['ID', 'Domain', 'Difficulty', 'Groundedness', 'Faithfulness', 'Hallucination', 'Trust'].map(h => (
                      <th key={h} style={{ textAlign: 'left', padding: '6px 10px', fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', borderBottom: '1px solid var(--border)', fontWeight: 500 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {cases.map((c, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)' }}>{c.case_id}</td>
                      <td style={{ padding: '8px 10px', fontSize: 12 }}>{c.domain || '—'}</td>
                      <td style={{ padding: '8px 10px', fontSize: 12 }}>{c.difficulty || '—'}</td>
                      <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: c.groundedness >= 80 ? '#1D9E75' : '#EF9F27' }}>{Math.round(c.groundedness)}%</td>
                      <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: c.faithfulness >= 80 ? '#1D9E75' : '#EF9F27' }}>{Math.round(c.faithfulness)}%</td>
                      <td style={{ padding: '8px 10px' }}>
                        <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, fontFamily: 'var(--font-mono)', fontWeight: 600, background: c.hallucination_risk === 'Low' ? 'rgba(29,158,117,0.15)' : c.hallucination_risk === 'Medium' ? 'rgba(239,159,39,0.15)' : 'rgba(226,75,74,0.15)', color: c.hallucination_risk === 'Low' ? '#1D9E75' : c.hallucination_risk === 'Medium' ? '#EF9F27' : '#E24B4A' }}>
                          {c.hallucination_risk}
                        </span>
                      </td>
                      <td style={{ padding: '8px 10px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#1D9E75' }}>{Math.round(c.trust_score)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <div style={{ fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', textAlign: 'right' }}>
            run_id: {job?.run_id} · model: {stats.model} · {Math.round(stats.total_latency_ms / 1000)}s total
          </div>
        </>
      )}
    </div>
  )
}
