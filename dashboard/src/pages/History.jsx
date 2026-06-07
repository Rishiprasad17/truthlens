import React, { useState, useEffect } from 'react'
import { Card, SectionLabel, RiskBadge, Btn } from '../components/UI'

const HISTORY_KEY = 'tl_history'

export default function HistoryPage() {
  const [history, setHistory] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    setHistory(JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'))
  }, [])

  function clear() {
    localStorage.removeItem(HISTORY_KEY)
    setHistory([])
    setSelected(null)
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', height: '100%', overflow: 'hidden' }}>
      <div style={{ borderRight: '1px solid var(--border)', overflowY: 'auto', padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <SectionLabel>History ({history.length})</SectionLabel>
          {history.length > 0 && (
            <button onClick={clear} style={{ fontSize: 11, color: 'var(--muted)', background: 'transparent', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-mono)' }}>clear</button>
          )}
        </div>
        {history.length === 0 && (
          <div style={{ color: 'var(--muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }}>// no evaluations yet</div>
        )}
        {history.map((item, i) => (
          <div key={i} onClick={() => setSelected(item)} style={{
            padding: '10px 12px', borderRadius: 'var(--radius-sm)', marginBottom: 6, cursor: 'pointer',
            background: selected === item ? 'var(--accent-dim)' : 'var(--surface2)',
            border: `1px solid ${selected === item ? 'var(--accent-border)' : 'var(--border)'}`,
            transition: 'all 0.12s',
          }}>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {item.question}
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: '#1D9E75' }}>{Math.round(item.trust_score)}/100</span>
              <RiskBadge risk={item.hallucination_risk} />
            </div>
            <div style={{ fontSize: 10, color: 'var(--muted)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
              {new Date(item.savedAt).toLocaleString()}
            </div>
          </div>
        ))}
      </div>

      <div style={{ overflowY: 'auto', padding: '1.25rem' }}>
        {!selected && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--muted)', fontSize: 13, fontFamily: 'var(--font-mono)' }}>
            // select an evaluation to view details
          </div>
        )}
        {selected && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <SectionLabel>Evaluation Detail</SectionLabel>
            <Card>
              <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Question</div>
              <div style={{ fontSize: 14, fontFamily: 'var(--font-mono)' }}>{selected.question}</div>
            </Card>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
              {[
                ['Groundedness', selected.groundedness],
                ['Faithfulness', selected.faithfulness],
                ['Citations', selected.citation_accuracy],
                ['Trust', selected.trust_score],
              ].map(([l, v]) => (
                <div key={l} style={{ background: 'var(--surface2)', borderRadius: 'var(--radius-sm)', padding: '12px', textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 800, color: '#1D9E75', fontFamily: 'var(--font-mono)' }}>{Math.round(v)}%</div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{l}</div>
                </div>
              ))}
            </div>
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>Hallucination Risk</span>
                <RiskBadge risk={selected.hallucination_risk} />
              </div>
              <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>
                <span>model: {selected.model}</span>
                <span>latency: {Math.round(selected.latency_ms)}ms</span>
              </div>
            </Card>
            {selected.unsupported_claims?.length > 0 && (
              <Card>
                <SectionLabel>Unsupported Claims</SectionLabel>
                {selected.unsupported_claims.map((c, i) => (
                  <div key={i} style={{ background: 'rgba(226,75,74,0.08)', border: '1px solid rgba(226,75,74,0.2)', borderRadius: 'var(--radius-sm)', padding: '8px 12px', marginBottom: 6, fontSize: 12, fontFamily: 'var(--font-mono)', color: '#E24B4A' }}>
                    ↳ {c}
                  </div>
                ))}
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
