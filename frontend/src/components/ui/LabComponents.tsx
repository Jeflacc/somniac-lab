import React from 'react'

export function StatBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100)
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12 }}>
        <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
        <span className="mono" style={{ color, fontSize: 11 }}>{pct}%</span>
      </div>
      <div className="stat-bar-track">
        <div className="stat-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

export function barColor(v: number): string {
  if (v < 0.4) return 'var(--green)'
  if (v < 0.7) return 'var(--yellow)'
  return 'var(--red)'
}

export function MoodBadge({ mood }: { mood: string }) {
  const map: Record<string, { emoji: string; color: string; bg: string }> = {
    happy:   { emoji: '😊', color: '#34d399', bg: 'rgba(52,211,153,0.15)' },
    sad:     { emoji: '😢', color: '#60a5fa', bg: 'rgba(96,165,250,0.15)' },
    angry:   { emoji: '😠', color: '#f87171', bg: 'rgba(248,113,113,0.15)' },
    neutral: { emoji: '😐', color: '#8888aa', bg: 'rgba(136,136,170,0.15)' },
  }
  const m = map[mood?.toLowerCase()] || map.neutral
  return (
    <span className="badge" style={{ background: m.bg, color: m.color, border: `1px solid ${m.color}33` }}>
      {m.emoji} {mood || 'Neutral'}
    </span>
  )
}

export function AgentAvatar({ src, name, size = 40, className = '' }: { src?: string | null; name: string; size?: number; className?: string }) {
  if (src) {
    return <img src={src} alt={name} className={className} style={{ width: size, height: size, borderRadius: '50%', objectFit: 'cover', flexShrink: 0, background: 'var(--bg-panel)' }} />
  }
  const initial = (name || '?')[0].toUpperCase()
  const hue = name.split('').reduce((a, c) => a + c.charCodeAt(0), 0) % 360
  return (
    <div className={className} style={{
      width: size, height: size, borderRadius: '50%', background: `hsl(${hue}, 40%, 30%)`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: `hsl(${hue}, 60%, 75%)`, fontWeight: 700, fontSize: size * 0.4, flexShrink: 0,
    }}>
      {initial}
    </div>
  )
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      textTransform: 'uppercase', fontSize: 10, fontWeight: 700,
      letterSpacing: '0.1em', color: 'var(--text-muted)',
      paddingBottom: 6, borderBottom: '1px solid var(--border)',
    }}>
      {children}
    </div>
  )
}

export function QuickBtn({ onClick, icon, label }: { onClick: () => void; icon: string; label: string }) {
  return (
    <button onClick={onClick} style={{
      background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8,
      padding: '8px 12px', color: 'var(--text-secondary)', fontSize: 12, fontWeight: 500,
      cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, textAlign: 'left',
      transition: 'all 0.15s', width: '100%',
    }}
    onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--text-primary)' }}
    onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)' }}
    >
      <span>{icon}</span> {label}
    </button>
  )
}

export function EvelynEye({ size = 36, sleeping = false }: { size?: number; sleeping?: boolean }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" style={{ animation: sleeping ? 'none' : 'blink 5s infinite', flexShrink: 0 }}>
      <ellipse cx="50" cy="50" rx="44" ry="44" fill="none" stroke="var(--accent)" strokeWidth="4" />
      <ellipse cx="50" cy="50" rx="26" ry="26" fill="var(--accent)" opacity="0.15" />
      {sleeping ? (
        <ellipse cx="50" cy="55" rx="18" ry="4" fill="var(--accent)" opacity="0.5" />
      ) : (
        <>
          <circle cx="50" cy="50" r="18" fill="var(--accent)" />
          <circle cx="50" cy="50" r="9" fill="var(--bg-primary)" />
          <circle cx="44" cy="44" r="4" fill="rgba(255,255,255,0.5)" />
        </>
      )}
    </svg>
  )
}
