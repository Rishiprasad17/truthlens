import React from 'react'

export function ScoreBar({ value, max = 100, color }) {
  const pct = Math.min(100, (value / max) * 100)
  const c = color || (pct >= 85 ? '#1D9E75' : pct >= 65 ? '#EF9F27' : '#E24B4A')
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{
        flex: 1, height: 4, background: 'rgba(255,255,255,0.08)',
        borderRadius: 2, overflow: 'hidden'
      }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: c, borderRadius: 2,
          transition: 'width 0.6s cubic-bezier(0.4,0,0.2,1)'
        }} />
      </div>
      <span style={{
        fontFamily: 'var(--font-mono)', fontSize: 12,
        color: c, minWidth: 36, textAlign: 'right', fontWeight: 500
      }}>
        {typeof value === 'number' ? `${Math.round(value)}%` : value}
      </span>
    </div>
  )
}

export function RiskBadge({ risk }) {
  const map = {
    Low:    { bg: 'rgba(29,158,117,0.15)', color: '#1D9E75' },
    Medium: { bg: 'rgba(239,159,39,0.15)',  color: '#EF9F27' },
    High:   { bg: 'rgba(226,75,74,0.15)',   color: '#E24B4A' },
  }
  const style = map[risk] || map.Medium
  return (
    <span style={{
      padding: '3px 10px', borderRadius: 20,
      fontSize: 11, fontWeight: 600, fontFamily: 'var(--font-mono)',
      background: style.bg, color: style.color,
      border: `1px solid ${style.color}33`,
    }}>
      {risk}
    </span>
  )
}

export function Card({ children, style }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '1.25rem',
      ...style,
    }}>
      {children}
    </div>
  )
}

export function MetricCard({ label, value, sub, color }) {
  return (
    <div style={{
      background: 'var(--surface2)',
      borderRadius: 'var(--radius-sm)',
      padding: '14px 16px',
      textAlign: 'center',
    }}>
      <div style={{
        fontSize: 24, fontWeight: 800, lineHeight: 1,
        color: color || '#1D9E75', marginBottom: 4,
        fontFamily: 'var(--font-mono)',
      }}>
        {value}
      </div>
      <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        {label}
      </div>
      {sub && <div style={{ fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

export function SectionLabel({ children }) {
  return (
    <div style={{
      fontSize: 11, fontWeight: 600, letterSpacing: '0.1em',
      textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12,
    }}>
      {children}
    </div>
  )
}

export function Btn({ children, onClick, primary, disabled, style }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '9px 18px',
        borderRadius: 'var(--radius-sm)',
        fontSize: 13, fontWeight: 600,
        fontFamily: 'var(--font-sans)',
        background: primary ? '#1D9E75' : 'transparent',
        color: primary ? '#fff' : 'var(--text)',
        border: primary ? '1px solid #1D9E75' : '1px solid var(--border2)',
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s',
        ...style,
      }}
    >
      {children}
    </button>
  )
}

export function Spinner() {
  return (
    <div style={{
      width: 20, height: 20, borderRadius: '50%',
      border: '2px solid var(--border2)',
      borderTopColor: 'var(--accent)',
      animation: 'spin 0.7s linear infinite',
      display: 'inline-block',
    }} />
  )
}
