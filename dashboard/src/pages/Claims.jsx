import React, { useState } from 'react'
import { api } from '../api'
import { Card, SectionLabel, Btn, Spinner } from '../components/UI'

const VERDICT_STYLE = {
  Supported:    { bg: 'rgba(29,158,117,0.1)',  border: 'rgba(29,158,117,0.3)',  color: '#1D9E75', icon: '✓' },
  Unsupported:  { bg: 'rgba(239,159,39,0.1)',  border: 'rgba(239,159,39,0.3)',  color: '#EF9F27', icon: '?' },
  Contradicted: { bg: 'rgba(226,75,74,0.1)',   border: 'rgba(226,75,74,0.3)',   color: '#E24B4A', icon: '✗' },
}

function ClaimCard({ claim, index }) {
  const [open, setOpen] = useState(false)
  const s = VERDICT_STYLE[claim.verdict] || VERDICT_STYLE.Unsupported
  return (
    <div style={{
      background: s.bg, border: `1px solid ${s.border}`,
      borderRadius: 8, padding: '12px 14px', marginBottom: 8, cursor: 'pointer',
    }} onClick={() => setOpen(o => !o)}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <span style={{ color: s.color, fontWeight: 700, fontSize: 15, lineHeight: 1.4, flexShrink: 0 }}>
          {s.icon}
        </span>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13, lineHeight: 1.5, color: 'var(--text)' }}>{claim.text}</span>
            <span style={{
              fontSize: 11, fontFamily: 'var(--font-mono)', color: s.color,
              background: s.bg, border: `1px solid ${s.border}`,
              padding: '2px 8px', borderRadius: 12, flexShrink: 0, fontWeight: 600,
            }}>
              {claim.verdict}
            </span>
          </div>

          {open && (
            <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {claim.evidence && (
                <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--muted)', background: 'rgba(255,255,255,0.04)', borderRadius: 4, padding: '6px 10px', lineHeight: 1.6 }}>
                  <span style={{ color: s.color, fontWeight: 600 }}>Evidence: </span>{claim.evidence}
                </div>
              )}
              {claim.reasoning && (
                <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.5 }}>
                  <span style={{ color: 'var(--text)', fontWeight: 600 }}>Reasoning: </span>{claim.reasoning}
                </div>
              )}
              <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--muted)' }}>
                Confidence: {Math.round(claim.confidence)}%
                {claim.source_index != null && ` · Source ${claim.source_index + 1}`}
              </div>
            </div>
          )}
        </div>
        <span style={{ color: 'var(--muted)', fontSize: 11, flexShrink: 0, marginTop: 2 }}>
          {open ? '▲' : '▼'}
        </span>
      </div>
    </div>
  )
}

export default function ClaimsPage() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState('')
  const [model, setModel] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [report, setReport] = useState(null)

  async function run() {
    if (!question || !answer || !sources) { setError('Fill in all fields.'); return }
    setLoading(true); setError(null)
    try {
      const r = await fetch('/api/evaluate/claims', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question, answer,
          sources: sources.split('\n---\n').map(s => s.trim()).filter(Boolean),
          model: model || undefined,
        })
      })
      if (!r.ok) { const e = await r.json(); throw new Error(e.detail) }
      setReport(await r.json())
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  const verdictColor = report
    ? report.overall_verdict === 'Trustworthy' ? '#1D9E75'
    : report.overall_verdict === 'Partially Trustworthy' ? '#EF9F27' : '#E24B4A'
    : '#1D9E75'

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '1.5rem', padding: '1.5rem', height: '100%', overflowY: 'auto' }}>

      {/* Input */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <SectionLabel>Claim Verification</SectionLabel>
        <div style={{ fontSize: 12, color: 'var(--muted)', fontFamily: 'var(--font-mono)', lineHeight: 1.6, background: 'var(--surface2)', borderRadius: 6, padding: '10px 12px' }}>
          Phase 2 — breaks the answer into atomic claims and verifies each one as Supported / Unsupported / Contradicted.
        </div>

        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Question</label>
          <input value={question} onChange={e => setQuestion(e.target.value)} placeholder="What caused the 2008 financial crisis?" />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>AI Answer</label>
          <textarea value={answer} onChange={e => setAnswer(e.target.value)} rows={6} placeholder="Paste the AI answer to verify..." style={{ resize: 'vertical' }} />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Sources <span style={{ opacity: 0.5 }}>(separate with ---)</span></label>
          <textarea value={sources} onChange={e => setSources(e.target.value)} rows={5} placeholder={"Source 1...\n---\nSource 2..."} style={{ resize: 'vertical' }} />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Model</label>
          <input value={model} onChange={e => setModel(e.target.value)} placeholder="llama3..." />
        </div>

        {error && <div style={{ color: '#E24B4A', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{error}</div>}

        <Btn primary onClick={run} disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading
            ? <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Spinner /> Verifying claims…</span>
            : 'Verify Claims →'}
        </Btn>
      </div>

      {/* Results */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <SectionLabel>Claim Breakdown</SectionLabel>

        {!report && !loading && (
          <Card style={{ minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontSize: 13, fontFamily: 'var(--font-mono)' }}>
            // awaiting claim verification
          </Card>
        )}

        {loading && (
          <Card style={{ minHeight: 300, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16, color: 'var(--muted)' }}>
            <Spinner />
            <div style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 13, lineHeight: 1.8 }}>
              <div>Extracting claims…</div>
              <div style={{ opacity: 0.6, fontSize: 11 }}>Verifying each one against sources</div>
            </div>
          </Card>
        )}

        {report && (
          <>
            {/* Summary bar */}
            <Card>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>Overall Verdict</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: verdictColor }}>{report.overall_verdict}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 32, fontWeight: 800, color: verdictColor, fontFamily: 'var(--font-mono)', lineHeight: 1 }}>{Math.round(report.trust_score)}</div>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>/ 100</div>
                </div>
              </div>

              {/* Stacked bar */}
              <div style={{ display: 'flex', height: 8, borderRadius: 4, overflow: 'hidden', gap: 1, marginBottom: 12 }}>
                {report.supported_pct > 0 && <div style={{ flex: report.supported_pct, background: '#1D9E75', transition: 'flex 0.6s' }} />}
                {report.unsupported_pct > 0 && <div style={{ flex: report.unsupported_pct, background: '#EF9F27', transition: 'flex 0.6s' }} />}
                {report.contradicted_pct > 0 && <div style={{ flex: report.contradicted_pct, background: '#E24B4A', transition: 'flex 0.6s' }} />}
              </div>

              <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
                {[
                  ['✓ Supported', report.supported_count, report.supported_pct, '#1D9E75'],
                  ['? Unsupported', report.unsupported_count, report.unsupported_pct, '#EF9F27'],
                  ['✗ Contradicted', report.contradicted_count, report.contradicted_pct, '#E24B4A'],
                ].map(([label, count, pct, color]) => (
                  <div key={label}>
                    <span style={{ color, fontWeight: 600 }}>{count}</span>
                    <span style={{ color: 'var(--muted)', fontSize: 11, marginLeft: 4 }}>{label} ({pct}%)</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Per-claim list */}
            <Card>
              <SectionLabel>Claims ({report.total_claims}) — click to expand</SectionLabel>
              <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                {report.claims.map((claim, i) => (
                  <ClaimCard key={i} claim={claim} index={i + 1} />
                ))}
              </div>
            </Card>

            <div style={{ fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)', textAlign: 'right' }}>
              model: {report.model} · {Math.round(report.latency_ms)}ms
            </div>
          </>
        )}
      </div>
    </div>
  )
}
