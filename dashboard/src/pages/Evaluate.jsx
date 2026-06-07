import React, { useState } from 'react'
import { api } from '../api'
import { ScoreBar, RiskBadge, Card, MetricCard, SectionLabel, Btn, Spinner } from '../components/UI'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts'

const HISTORY_KEY = 'tl_history'
function saveHistory(report) {
  const h = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  h.unshift({ ...report, savedAt: new Date().toISOString() })
  localStorage.setItem(HISTORY_KEY, JSON.stringify(h.slice(0, 50)))
}

export default function EvaluatePage() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState('')
  const [model, setModel] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [report, setReport] = useState(null)

  async function run() {
    if (!question || !answer || !sources) {
      setError('Please fill in question, answer, and at least one source.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const r = await api.evaluate({
        question,
        answer,
        sources: sources.split('\n---\n').map(s => s.trim()).filter(Boolean),
        model: model || undefined,
      })
      setReport(r)
      saveHistory(r)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const radarData = report ? [
    { metric: 'Groundedness',  value: report.groundedness },
    { metric: 'Faithfulness',  value: report.faithfulness },
    { metric: 'Citations',     value: report.citation_accuracy },
    { metric: 'Consistency',   value: report.consistency_score },
    { metric: 'Trust',         value: report.trust_score },
  ] : []

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', padding: '1.5rem', height: '100%', overflowY: 'auto' }}>
      {/* Input panel */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <SectionLabel>Evaluation Input</SectionLabel>

        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Question</label>
          <input value={question} onChange={e => setQuestion(e.target.value)} placeholder="What caused the 2008 financial crisis?" />
        </div>

        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>AI Answer</label>
          <textarea value={answer} onChange={e => setAnswer(e.target.value)}
            placeholder="Paste the AI-generated answer here..."
            rows={5} style={{ resize: 'vertical' }} />
        </div>

        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Source Documents <span style={{ opacity: 0.5 }}>(separate with ---)</span>
          </label>
          <textarea value={sources} onChange={e => setSources(e.target.value)}
            placeholder={"Source 1 text here...\n---\nSource 2 text here..."}
            rows={6} style={{ resize: 'vertical' }} />
        </div>

        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Model (optional)</label>
          <input value={model} onChange={e => setModel(e.target.value)} placeholder="llama3 / mistral / gemma..." />
        </div>

        {error && (
          <div style={{ background: 'rgba(226,75,74,0.1)', border: '1px solid rgba(226,75,74,0.3)', borderRadius: 'var(--radius-sm)', padding: '10px 14px', fontSize: 13, color: '#E24B4A', fontFamily: 'var(--font-mono)' }}>
            {error}
          </div>
        )}

        <Btn primary onClick={run} disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Spinner /> Evaluating…</span> : 'Run Evaluation →'}
        </Btn>
      </div>

      {/* Results panel */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <SectionLabel>Results</SectionLabel>

        {!report && !loading && (
          <Card style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300, color: 'var(--muted)', fontSize: 13, fontFamily: 'var(--font-mono)' }}>
            // run an evaluation to see results
          </Card>
        )}

        {loading && (
          <Card style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300, gap: 12, color: 'var(--muted)' }}>
            <Spinner /> <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>Evaluating with Ollama…</span>
          </Card>
        )}

        {report && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
              <MetricCard label="Groundedness" value={`${Math.round(report.groundedness)}%`} />
              <MetricCard label="Faithfulness" value={`${Math.round(report.faithfulness)}%`} />
              <MetricCard label="Trust Score" value={`${Math.round(report.trust_score)}`} />
            </div>

            <Card>
              <SectionLabel>Detailed Scores</SectionLabel>
              {[
                ['Groundedness', report.groundedness],
                ['Faithfulness', report.faithfulness],
                ['Citation Accuracy', report.citation_accuracy],
                ['Consistency', report.consistency_score],
              ].map(([label, val]) => (
                <div key={label} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12, color: 'var(--muted)' }}>
                    <span>{label}</span>
                  </div>
                  <ScoreBar value={val} />
                </div>
              ))}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>Hallucination Risk</span>
                <RiskBadge risk={report.hallucination_risk} />
              </div>
            </Card>

            <Card>
              <SectionLabel>Radar View</SectionLabel>
              <ResponsiveContainer width="100%" height={200}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.08)" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: '#888884', fontSize: 11 }} />
                  <Radar dataKey="value" stroke="#1D9E75" fill="#1D9E75" fillOpacity={0.15} />
                  <Tooltip
                    contentStyle={{ background: '#111', border: '1px solid #222', borderRadius: 6, fontFamily: 'DM Mono' }}
                    formatter={(v) => [`${Math.round(v)}%`]}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </Card>

            {report.unsupported_claims?.length > 0 && (
              <Card>
                <SectionLabel>Unsupported Claims</SectionLabel>
                {report.unsupported_claims.map((c, i) => (
                  <div key={i} style={{
                    background: 'rgba(226,75,74,0.08)', border: '1px solid rgba(226,75,74,0.2)',
                    borderRadius: 'var(--radius-sm)', padding: '8px 12px', marginBottom: 8,
                    fontSize: 12, fontFamily: 'var(--font-mono)', color: '#E24B4A', lineHeight: 1.5,
                  }}>
                    ↳ {c}
                  </div>
                ))}
              </Card>
            )}

            {report.latency_ms && (
              <div style={{ fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', textAlign: 'right' }}>
                model: {report.model} · latency: {Math.round(report.latency_ms)}ms
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
