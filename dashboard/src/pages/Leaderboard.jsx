import React, { useState, useRef, useEffect } from 'react'
import { Card, SectionLabel, Btn, Spinner } from '../components/UI'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend } from 'recharts'

const MODEL_COLORS = ['#1D9E75', '#6B7FD7', '#EF9F27', '#E24B4A', '#A855F7', '#F472B6']

export default function LeaderboardPage() {
  const [models, setModels] = useState('llama3\nmistral')
  const [mode, setMode] = useState('sample')
  const [casesJson, setCasesJson] = useState('')
  const [jobId, setJobId] = useState(null)
  const [job, setJob] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const pollRef = useRef(null)

  useEffect(() => () => clearInterval(pollRef.current), [])

  async function start() {
    const modelList = models.split('\n').map(m => m.trim()).filter(Boolean)
    if (modelList.length < 1) { setError('Add at least one model.'); return }
    setLoading(true); setError(null); setJob(null)
    try {
      const body = {
        models: modelList,
        use_sample: mode === 'sample',
        cases: mode === 'custom' ? JSON.parse(casesJson) : undefined,
      }
      const res = await fetch('/api/leaderboard', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail) }
      const { job_id } = await res.json()
      setJobId(job_id)
      pollRef.current = setInterval(() => poll(job_id), 2000)
    } catch (e) { setError(e.message); setLoading(false) }
  }

  async function poll(id) {
    try {
      const res = await fetch(`/api/leaderboard/${id}`)
      const data = await res.json()
      setJob(data)
      if (data.status === 'done' || data.status === 'error') {
        clearInterval(pollRef.current)
        setLoading(false)
      }
    } catch {}
  }

  const lb = job?.result?.leaderboard || []
  const radarData = lb.map(e => ({
    model: e.model,
    trust: e.avg_trust_score,
    ground: e.avg_groundedness,
    faith: e.avg_faithfulness,
    citations: e.avg_citation_accuracy,
  }))

  const barData = lb.map(e => ({ model: e.model, trust: Math.round(e.avg_trust_score) }))

  return (
    <div style={{ padding: '1.5rem', overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <SectionLabel>Model Leaderboard — Phase 4</SectionLabel>

      <Card>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Models to Compare (one per line)</label>
            <textarea value={models} onChange={e => setModels(e.target.value)} rows={5}
              style={{ fontFamily: 'var(--font-mono)', fontSize: 13, resize: 'vertical' }}
              placeholder={"llama3\nmistral\ngemma"} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div>
              <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Dataset</label>
              <div style={{ display: 'flex', gap: 8 }}>
                {['sample', 'custom'].map(m => (
                  <button key={m} onClick={() => setMode(m)} style={{
                    padding: '7px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                    background: mode === m ? '#1D9E75' : 'transparent',
                    color: mode === m ? '#fff' : 'var(--muted)',
                    border: `1px solid ${mode === m ? '#1D9E75' : 'var(--border)'}`,
                    cursor: 'pointer',
                  }}>{m === 'sample' ? 'Sample (5 cases)' : 'Custom JSON'}</button>
                ))}
              </div>
            </div>
            {mode === 'custom' && (
              <textarea value={casesJson} onChange={e => setCasesJson(e.target.value)} rows={4}
                style={{ fontFamily: 'var(--font-mono)', fontSize: 11, resize: 'vertical' }}
                placeholder='[{"id":"1","question":"...","answer":"...","sources":["..."]}]' />
            )}
          </div>
        </div>

        <Btn primary onClick={start} disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Spinner /> Running leaderboard…</span> : 'Run Leaderboard →'}
        </Btn>

        {loading && job && (
          <div style={{ marginTop: '1rem', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>
            Evaluating: <span style={{ color: '#1D9E75' }}>{job.current_model}</span>
            {job.total > 0 && ` — case ${job.progress}/${job.total}`}
          </div>
        )}
        {error && <div style={{ marginTop: 10, color: '#E24B4A', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{error}</div>}
      </Card>

      {job?.status === 'done' && lb.length > 0 && (
        <>
          <div style={{ background: 'rgba(29,158,117,0.08)', border: '1px solid rgba(29,158,117,0.3)', borderRadius: 8, padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
            🏆 <span style={{ color: '#1D9E75', fontWeight: 700 }}>Winner: {job.result.winner}</span>
            {job.result.domain_winners && Object.keys(job.result.domain_winners).length > 0 && (
              <span style={{ color: 'var(--muted)', marginLeft: 16, fontSize: 11 }}>
                Domain wins: {Object.entries(job.result.domain_winners).map(([d, m]) => `${d}→${m}`).join(', ')}
              </span>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            <Card>
              <SectionLabel>Trust Score Ranking</SectionLabel>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={barData} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
                  <XAxis dataKey="model" tick={{ fill: '#888884', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#888884', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#111', border: '1px solid #222', borderRadius: 6, fontFamily: 'DM Mono', fontSize: 12 }} />
                  <Bar dataKey="trust" name="Trust Score" radius={[4, 4, 0, 0]}>
                    {barData.map((e, i) => <Cell key={i} fill={e.model === job.result.winner ? '#1D9E75' : '#2a2a2a'} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card>
              <SectionLabel>Multi-Metric Comparison</SectionLabel>
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={[
                  { metric: 'Trust', ...Object.fromEntries(lb.map(e => [e.model, e.avg_trust_score])) },
                  { metric: 'Groundedness', ...Object.fromEntries(lb.map(e => [e.model, e.avg_groundedness])) },
                  { metric: 'Faithfulness', ...Object.fromEntries(lb.map(e => [e.model, e.avg_faithfulness])) },
                  { metric: 'Low Risk %', ...Object.fromEntries(lb.map(e => [e.model, e.low_risk_pct])) },
                ]}>
                  <PolarGrid stroke="rgba(255,255,255,0.08)" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: '#888884', fontSize: 11 }} />
                  {lb.map((e, i) => (
                    <Radar key={e.model} name={e.model} dataKey={e.model} stroke={MODEL_COLORS[i % MODEL_COLORS.length]} fill={MODEL_COLORS[i % MODEL_COLORS.length]} fillOpacity={0.1} />
                  ))}
                  <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'DM Mono' }} />
                  <Tooltip contentStyle={{ background: '#111', border: '1px solid #222', borderRadius: 6, fontFamily: 'DM Mono', fontSize: 12 }} />
                </RadarChart>
              </ResponsiveContainer>
            </Card>
          </div>

          <Card>
            <SectionLabel>Full Leaderboard</SectionLabel>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  {['Rank', 'Model', 'Trust Score', 'Groundedness', 'Faithfulness', 'Citations', 'Low Risk %', 'Latency'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '6px 10px', fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', borderBottom: '1px solid var(--border)', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {lb.map((e, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>#{e.rank}</td>
                    <td style={{ padding: '10px', fontWeight: 700, color: e.model === job.result.winner ? '#1D9E75' : 'var(--text)' }}>
                      {e.model === job.result.winner ? '★ ' : ''}{e.model}
                    </td>
                    <td style={{ padding: '10px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#1D9E75', fontSize: 14 }}>{e.avg_trust_score.toFixed(1)}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>{e.avg_groundedness.toFixed(1)}%</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>{e.avg_faithfulness.toFixed(1)}%</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>{e.avg_citation_accuracy.toFixed(1)}%</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: '#1D9E75' }}>{e.low_risk_pct.toFixed(1)}%</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>{Math.round(e.avg_latency_ms)}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </div>
  )
}
