import React, { useState } from 'react'
import { api } from '../api'
import { ScoreBar, Card, MetricCard, SectionLabel, Btn, Spinner } from '../components/UI'

export default function RAGPage() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [chunks, setChunks] = useState('')
  const [model, setModel] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [report, setReport] = useState(null)

  async function run() {
    if (!question || !answer || !chunks) { setError('Fill all fields.'); return }
    setLoading(true); setError(null)
    try {
      const r = await api.evaluateRag({
        question, answer,
        retrieved_chunks: chunks.split('\n---\n').map(s => s.trim()).filter(Boolean),
        model: model || undefined,
      })
      setReport(r)
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', padding: '1.5rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <SectionLabel>RAG Pipeline Evaluation</SectionLabel>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Question</label>
          <input value={question} onChange={e => setQuestion(e.target.value)} placeholder="User query..." />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Retrieved Chunks <span style={{ opacity: 0.5 }}>(separate with ---)</span></label>
          <textarea value={chunks} onChange={e => setChunks(e.target.value)} placeholder={"Chunk 1...\n---\nChunk 2..."} rows={7} style={{ resize: 'vertical' }} />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Generated Answer</label>
          <textarea value={answer} onChange={e => setAnswer(e.target.value)} placeholder="LLM-generated answer..." rows={5} style={{ resize: 'vertical' }} />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Model</label>
          <input value={model} onChange={e => setModel(e.target.value)} placeholder="llama3..." />
        </div>
        {error && <div style={{ color: '#E24B4A', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{error}</div>}
        <Btn primary onClick={run} disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Spinner /> Evaluating…</span> : 'Evaluate RAG →'}
        </Btn>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <SectionLabel>Results</SectionLabel>
        {!report && !loading && (
          <Card style={{ minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontSize: 13, fontFamily: 'var(--font-mono)' }}>
            // awaiting RAG evaluation
          </Card>
        )}
        {loading && (
          <Card style={{ minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, color: 'var(--muted)' }}>
            <Spinner /><span style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>Analyzing pipeline…</span>
          </Card>
        )}
        {report && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
              <MetricCard label="Precision" value={`${Math.round(report.retrieval_precision)}%`} />
              <MetricCard label="Recall" value={`${Math.round(report.retrieval_recall)}%`} />
              <MetricCard label="RAG Score" value={`${Math.round(report.rag_score)}`} />
            </div>
            <Card>
              <SectionLabel>Pipeline Metrics</SectionLabel>
              {[
                ['Retrieval Precision', report.retrieval_precision],
                ['Retrieval Recall', report.retrieval_recall],
                ['Context Utilization', report.context_utilization],
                ['Evidence Coverage', report.evidence_coverage],
                ['Answer Relevance', report.answer_relevance],
              ].map(([label, val]) => (
                <div key={label} style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 4 }}>{label}</div>
                  <ScoreBar value={val} />
                </div>
              ))}
            </Card>
            {report.reasoning && Object.keys(report.reasoning).length > 0 && (
              <Card>
                <SectionLabel>Reasoning</SectionLabel>
                {Object.entries(report.reasoning).map(([k, v]) => (
                  <div key={k} style={{ marginBottom: 10 }}>
                    <div style={{ fontSize: 11, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>{k.replace(/_/g, ' ')}</div>
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
