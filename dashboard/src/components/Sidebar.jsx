import React from 'react'
import { NavLink } from 'react-router-dom'

const links = [
  { to: '/',            icon: '◈', label: 'Evaluate'   },
  { to: '/claims',      icon: '⊡', label: 'Claims'      },
  { to: '/rag',         icon: '⟳', label: 'RAG Eval'   },
  { to: '/agent',       icon: '◎', label: 'Agent Eval'  },
  { to: '/compare',     icon: '⊞', label: 'Compare'     },
  { to: '/benchmark',   icon: '⊟', label: 'Benchmark'   },
  { to: '/leaderboard', icon: '◉', label: 'Leaderboard' },
  { to: '/proxy',       icon: '⇄', label: 'Proxy'       },
  { to: '/paper',       icon: '▦', label: 'Paper'       },
  { to: '/history',     icon: '▤', label: 'History'     },
]

export default function Sidebar() {
  return (
    <aside style={{
      width: 200, flexShrink: 0,
      borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      padding: '1.5rem 0',
      background: 'var(--surface)',
    }}>
      <div style={{ padding: '0 1.25rem 1.5rem', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em' }}>
          Truth<span style={{ color: '#1D9E75' }}>Lens</span>
        </div>
      </div>
      <nav style={{ flex: 1, padding: '1rem 0.75rem', overflowY: 'auto' }}>
        {links.map(({ to, icon, label }) => (
          <NavLink key={to} to={to} end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '7px 12px', borderRadius: 'var(--radius-sm)',
              color: isActive ? '#1D9E75' : 'var(--muted)',
              background: isActive ? 'rgba(29,158,117,0.1)' : 'transparent',
              fontWeight: isActive ? 600 : 400, fontSize: 13,
              textDecoration: 'none', marginBottom: 2, transition: 'all 0.12s',
            })}>
            <span style={{ fontSize: 14, lineHeight: 1 }}>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--border)' }}>
        <a href="https://github.com/yourorg/truthlens" target="_blank" rel="noreferrer"
          style={{ fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>
          github ↗
        </a>
      </div>
    </aside>
  )
}

