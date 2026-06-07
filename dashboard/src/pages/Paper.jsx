import React, { useState, useEffect } from 'react'
import { Card, SectionLabel, Btn, Spinner } from '../components/UI'

export default function PaperPage() {
  const [title, setTitle] = useState('TruthLens: A Unified Framework for Measuring Trustworthiness in Large Language Models and Retrieval-Augmented Systems')
  const [authors, setAuthors] = useState('')
  const [runId, setRunId] = useState('')
  const [format, setFormat] = useState('markdown')
  const [loading, setLoading] = useState(false)
  const [paper, setPaper] = useState(null)
  const [error, setError] = useState(null)
  const [reports, setReports] = useState([])

  useEffect(() => {
    fetch('/api/reports').then(r => r.json()).then(d => setReports(d.reports || [])).catch(() => {})
  }, [])

  async function generate() {
    setLoading(true); setError(null)
    try {
      const res = await fetch('/api/paper', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, authors: authors || undefined, run_id: runId || undefined, output_format: format }),
      })
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail) }
      const data = await res.json()
      setPaper(data.paper)
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  function download() {
    const ext = format === 'latex' ? 'tex' : 'md'
    const blob = new Blob([paper], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `truthlens_paper.${ext}`
    a.click(); URL.revokeObjectURL(url)
  }

  function copy() {
    navigator.clipboard.writeText(paper)
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', height: '100%', overflow: 'hidden' }}>
      <div style={{ borderRight: '1px solid var(--border)', padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <SectionLabel>Paper Generator</SectionLabel>

        <div style={{ fontSize: 12, color: 'var(--muted)', fontFamily: 'var(--font-mono)', lineHeight: 1.6, background: 'var(--surface2)', borderRadius: 6, padding: '10px 12px' }}>
          Generates a full research paper draft populated with your real benchmark data.
        </div>

        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Title</label>
          <textarea value={title} onChange={e => setTitle(e.target.value)} rows={3} style={{ resize: 'vertical', fontSize: 12 }} />
        </div>

        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Authors</label>
          <input value={authors} onChange={e => setAuthors(e.target.value)} placeholder="Your name, institution" />
        </div>

        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Benchmark Run (optional)</label>
          {reports.length > 0 ? (
            <select value={runId} onChange={e => setRunId(e.target.value)}>
              <option value="">None (empty template)</option>
              {reports.map(r => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} — {r.total_cases} cases, trust {r.avg_trust_score}
                </option>
              ))}
            </select>
          ) : (
            <input value={runId} onChange={e => setRunId(e.target.value)} placeholder="run_id from benchmark..." />
          )}
        </div>

        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Format</label>
          <div style={{ display: 'flex', gap: 8 }}>
            {['markdown', 'latex'].map(f => (
              <button key={f} onClick={() => setFormat(f)} style={{
                padding: '7px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                background: format === f ? '#1D9E75' : 'transparent',
                color: format === f ? '#fff' : 'var(--muted)',
                border: `1px solid ${format === f ? '#1D9E75' : 'var(--border)'}`,
                cursor: 'pointer',
              }}>{f}</button>
            ))}
          </div>
        </div>

        {error && <div style={{ color: '#E24B4A', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{error}</div>}

        <Btn primary onClick={generate} disabled={loading}>
          {loading ? <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Spinner /> Generating…</span> : 'Generate Paper →'}
        </Btn>

        {paper && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <Btn onClick={download} style={{ width: '100%', textAlign: 'center' }}>
              ↓ Download .{format === 'latex' ? 'tex' : 'md'}
            </Btn>
            <Btn onClick={copy} style={{ width: '100%', textAlign: 'center' }}>
              Copy to clipboard
            </Btn>
          </div>
        )}
      </div>

      <div style={{ overflowY: 'auto', padding: '1.5rem' }}>
        {!paper && !loading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--muted)', fontSize: 13, fontFamily: 'var(--font-mono)' }}>
            // configure and generate your paper
          </div>
        )}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 12, color: 'var(--muted)' }}>
            <Spinner /> <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>Generating paper…</span>
          </div>
        )}
        {paper && (
          <pre style={{
            fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.8,
            color: 'var(--text)', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 8, padding: '1.5rem',
          }}>
            {paper}
          </pre>
        )}
      </div>
    </div>
  )
}
