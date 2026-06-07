import React, { useState } from 'react'
import { api } from '../api'
import { ScoreBar, Card, MetricCard, SectionLabel, Btn, Spinner } from '../components/UI'

const defaultTrace = JSON.stringify([
  { thought: "I need to search for recent data", tool: "web_search", input: "Q3 2024 revenue", output: "Revenue was $4.2B..." },
  { thought: "Now I'll calculate growth", tool: "calculator", input: "4.2 / 3.8 - 1", output: "0.105" },
], null, 2)

export default function AgentPage() {
  const [task, setTask] = useState('')
  const [trace, setTrace] = useState(defaultTrace)
  const [output, setOutput] = useState('')
  const [model, setModel] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [report, setReport] = useState(null)

  async function run() {
    if (!task || !output) { setError('Fill task and final output.'); return }
    let parsedTrace = []
    try { parsedTrace = JSON.parse(trace) } catch { setError('Trace must be valid JSON.'); return }
    setLoading(true); setError(null)
    try {
      const r = await api.evaluateAgent({ task, agent_trace: parsedTrace, final_output: output, model: model || undefined })
      setReport(r)
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', padding: '1.5rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <SectionLabel>Agent Evaluation</SectionLabel>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Task Description</label>
          <textarea value={task} onChange={e => setTask(e.target.value)} placeholder="Analyze Q3 revenue and compare to Q2..." rows={3} style={{ resize: 'vertical' }} />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Agent Trace (JSON array)</label>
          <textarea value={trace} onChange={e => setTrace(e.target.value)} rows={10} style={{ resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: 12 }} />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Final Output</label>
          <textarea value={output} onChange={e => setOutput(e.target.value)} placeholder="The agent's final answer..." rows={3} style={{ resize: 'vertical' }} />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Model</label>
          <input value={model} onChange={e => setModel(e.target.value)} placeholder="llama3..." />
        </div>
        {error && <div style={{ color: '#E24B4A', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{error}</div>}
        <Btn primary onClick={run} disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Spinner /> Evaluating…</span> : 'Evaluate Agent →'}
        </Btn>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <SectionLabel>Results</SectionLabel>
        {!report && !loading && (
          <Card style={{ minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontSize: 13, fontFamily: 'var(--font-mono)' }}>
            // awaiting agent evaluation
          </Card>
        )}
        {loading && (
          <Card style={{ minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, color: 'var(--muted)' }}>
            <Spinner /><span style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>Tracing agent decisions…</span>
          </Card>
        )}
        {report && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
              <MetricCard label="Task Completion" value={`${Math.round(report.task_completion)}%`} />
              <MetricCard label="Agent Score" value={`${Math.round(report.agent_score)}`} />
            </div>
            <Card>
              <SectionLabel>Agent Metrics</SectionLabel>
              {[
                ['Tool Usage Accuracy', report.tool_usage_accuracy],
                ['Planning Quality', report.planning_quality],
                ['Task Completion', report.task_completion],
                ['Decision Tracing', report.decision_tracing_score],
              ].map(([label, val]) => (
                <div key={label} style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 4 }}>{label}</div>
                  <ScoreBar value={val} />
                </div>
              ))}
            </Card>
            {report.reasoning && (
              <Card>
                <SectionLabel>Reasoning</SectionLabel>
                {Object.entries(report.reasoning).map(([k, v]) => (
                  <div key={k} style={{ marginBottom: 10 }}>
                    <div style={{ fontSize: 11, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>{k.replace(/_/g,' ')}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6, fontFamily: 'var(--font-mono)' }}>{v}</div>
                  </div>
                ))}
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  )
}
