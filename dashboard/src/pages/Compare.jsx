import React, { useState } from 'react'
import { api } from '../api'
import { RiskBadge, Card, SectionLabel, Btn, Spinner } from '../components/UI'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function ComparePage() {
  const [question, setQuestion] = useState('')
  const [sources, setSources] = useState('')
  const [rows, setRows] = useState([
    { model: 'llama3', answer: '' },
    { model: 'mistral', answer: '' },
  ])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [report, setReport] = useState(null)

  function addRow() { setRows(r => [...r, { model: '', answer: '' }]) }
  function updateRow(i, field, val) {
    setRows(r => r.map((row, idx) => idx === i ? { ...row, [field]: val } : row))
  }

  async function run() {
    if (!question || !sources) { setError('Need question and sources.'); return }
    const answers = {}
    for (const row of rows) {
      if (row.model && row.answer) answers[row.model] = row.answer
    }
    if (Object.keys(answers).length < 2) { setError('Add at least 2 model answers.'); return }
    setLoading(true); setError(null)
    try {
      const r = await api.compare({
        question,
        answers,
        sources: sources.split('\n---\n').map(s => s.trim()).filter(Boolean),
      })
      setReport(r)
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  const chartData = report?.models?.map(m => ({
    model: m.model,
    trust: Math.round(m.trust_score),
    ground: Math.round(m.groundedness),
    faith: Math.round(m.faithfulness),
  })) || []

  return (
    <div style={{ padding: '1.5rem', overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <SectionLabel>Multi-Model Comparison</SectionLabel>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Question</label>
            <input value={question} onChange={e => setQuestion(e.target.value)} placeholder="The shared question for all models..." />
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Sources (separate with ---)</label>
            <textarea value={sources} onChange={e => setSources(e.target.value)} rows={4} style={{ resize: 'vertical' }} placeholder="Shared source documents..." />
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <label style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Model Answers</label>
          {rows.map((row, i) => (
            <div key={i} style={{ display: 'flex', gap: 8 }}>
              <input value={row.model} onChange={e => updateRow(i, 'model', e.target.value)}
                placeholder="model name" style={{ width: 120, flexShrink: 0 }} />
              <textarea value={row.answer} onChange={e => updateRow(i, 'answer', e.target.value)}
                placeholder="Model's answer..." rows={2} style={{ resize: 'vertical', flex: 1 }} />
            </div>
          ))}
          <button onClick={addRow} style={{ fontSize: 12, color: 'var(--accent)', background: 'transparent', border: '1px dashed var(--accent-border)', borderRadius: 'var(--radius-sm)', padding: '6px', cursor: 'pointer' }}>
            + add model
          </button>
        </div>
      </div>

      {error && <div style={{ color: '#E24B4A', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{error}</div>}

      <Btn primary onClick={run} disabled={loading} style={{ alignSelf: 'flex-start' }}>
        {loading ? <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Spinner /> Comparing…</span> : 'Compare Models →'}
      </Btn>

      {report && (
        <>
          <div style={{ background: 'rgba(29,158,117,0.08)', border: '1px solid var(--accent-border)', borderRadius: 'var(--radius-sm)', padding: '10px 16px', fontSize: 13, fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>
            🏆 Winner: <strong>{report.winner}</strong> — {report.reasoning}
          </div>

          <Card>
            <SectionLabel>Trust Scores Comparison</SectionLabel>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ top: 4, right: 16, left: -10, bottom: 4 }}>
                <XAxis dataKey="model" tick={{ fill: '#888884', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#888884', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#111', border: '1px solid #222', borderRadius: 6, fontFamily: 'DM Mono', fontSize: 12 }} />
                <Bar dataKey="trust" name="Trust Score" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.model === report.winner ? '#1D9E75' : '#333'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <SectionLabel>Detailed Breakdown</SectionLabel>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  {['Model', 'Groundedness', 'Faithfulness', 'Citations', 'Hallucination', 'Trust'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '6px 10px', fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', borderBottom: '1px solid var(--border)', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {report.models.map((m, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '10px', fontWeight: 600, color: m.model === report.winner ? '#1D9E75' : 'var(--text)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                      {m.model === report.winner ? '★ ' : ''}{m.model}
                    </td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>{Math.round(m.groundedness)}%</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>{Math.round(m.faithfulness)}%</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>{Math.round(m.citation_accuracy)}%</td>
                    <td style={{ padding: '10px' }}><RiskBadge risk={m.hallucination_risk} /></td>
                    <td style={{ padding: '10px', fontWeight: 700, color: '#1D9E75', fontFamily: 'var(--font-mono)', fontSize: 13 }}>{Math.round(m.trust_score)}</td>
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
