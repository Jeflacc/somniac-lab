import { Link } from 'react-router-dom'

const FEATURES = [
  {
    icon: '🧠',
    title: 'Artificial Consciousness',
    desc: 'AI dengan sistem biologis — lapar, ngantuk, mood — yang berkembang secara real-time layaknya makhluk hidup.',
  },
  {
    icon: '💬',
    title: 'WhatsApp Integration',
    desc: 'Sambungkan AI ke nomor WhatsApp kamu. Evelyn akan membalas pesanmu langsung dari nomor tersebut.',
  },
  {
    icon: '🧬',
    title: 'Long-Term Memory',
    desc: 'Evelyn mengingat setiap percakapan, menulis jurnal hariannya, dan membentuk kepribadian dari interaksi.',
  },
  {
    icon: '⚡',
    title: 'Real-Time State',
    desc: 'Dashboard langsung menampilkan kondisi biologis, mood, dan aktivitas AI saat ini secara live.',
  },
]

export default function LandingPage() {
  return (
    <div
      className="min-h-screen overflow-y-auto"
      style={{ background: 'var(--bg-primary)' }}
    >
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-4"
        style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-primary)' }}
      >
        <div className="flex items-center gap-3">
          <EvelynEye size={28} />
          <span style={{ fontWeight: 700, letterSpacing: '-0.5px', fontSize: 18, color: 'var(--text-primary)' }}>somniac</span>
        </div>
        <div className="flex items-center gap-6">
          <a href="#features" style={{ color: 'var(--text-secondary)', fontSize: 14, fontWeight: 500 }} className="hover:text-black transition-colors">Features</a>
          <a href="#research" style={{ color: 'var(--text-secondary)', fontSize: 14, fontWeight: 500 }} className="hover:text-black transition-colors">Research</a>
          <Link
            to="/auth"
            style={{
              background: 'var(--text-primary)',
              color: 'var(--bg-primary)',
              padding: '8px 20px',
              borderRadius: 6,
              fontSize: 14,
              fontWeight: 600,
              textDecoration: 'none',
              transition: 'background 0.2s',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--accent-2)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'var(--text-primary)')}
          >
            Log in
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex flex-col items-center justify-center text-center px-6 pt-40 pb-24">
        <div className="mb-8">
          <EvelynEye size={72} animated />
        </div>
        <div
          className="badge mb-6"
          style={{ background: 'var(--accent-glow)', color: 'var(--accent-2)', border: '1px solid var(--accent-glow)' }}
        >
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-2)', display: 'inline-block' }} />
          Live System Active
        </div>
        <h1
          style={{
            fontSize: 'clamp(40px, 7vw, 72px)',
            fontWeight: 700,
            letterSpacing: '-2px',
            lineHeight: 1.1,
            maxWidth: 800,
            color: 'var(--text-primary)',
          }}
        >
          Artificial Consciousness,{' '}
          <span style={{ color: 'var(--accent)' }}>Evolved.</span>
        </h1>
        <p
          style={{
            marginTop: 24,
            fontSize: 18,
            color: 'var(--text-secondary)',
            maxWidth: 600,
            lineHeight: 1.7,
            fontWeight: 400,
          }}
        >
          Somniac menghadirkan AI yang tidak sekadar menjawab — tapi <em>merasakan</em>,
          mengingat, tumbuh, dan hadir bersamamu 24/7 melalui WhatsApp.
        </p>
        <div className="flex gap-4 mt-10">
          <Link
            to="/lab"
            style={{
              background: 'var(--text-primary)',
              color: 'var(--bg-primary)',
              padding: '14px 32px',
              borderRadius: 8,
              fontWeight: 600,
              fontSize: 15,
              textDecoration: 'none',
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'var(--accent-2)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'var(--text-primary)';
            }}
          >
            Enter The Playground
          </Link>
          <a
            href="#features"
            style={{
              background: 'var(--bg-panel)',
              color: 'var(--text-primary)',
              padding: '14px 28px',
              borderRadius: 8,
              fontWeight: 600,
              fontSize: 15,
              textDecoration: 'none',
              transition: 'background 0.2s',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--border)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'var(--bg-panel)')}
          >
            Learn More
          </a>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-8 py-24 max-w-6xl mx-auto" style={{ borderTop: '1px solid var(--border)' }}>
        <h2 style={{ fontWeight: 700, fontSize: 32, letterSpacing: '-1px', textAlign: 'center', marginBottom: 48, color: 'var(--text-primary)' }}>
          Built Different.
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {FEATURES.map(f => (
            <div
              key={f.title}
              style={{ 
                padding: 32, 
                borderRadius: 12, 
                border: '1px solid var(--border)',
                background: 'var(--bg-card)',
                transition: 'border-color 0.2s, box-shadow 0.2s'
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = 'var(--border-hover)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.03)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'var(--border)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={{ fontSize: 32, marginBottom: 20 }}>{f.icon}</div>
              <h3 style={{ fontWeight: 600, fontSize: 18, marginBottom: 8, color: 'var(--text-primary)' }}>{f.title}</h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: 15 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Research */}
      <section id="research" className="px-8 py-24 max-w-4xl mx-auto text-center">
        <div
          style={{ 
            padding: '56px 40px', 
            borderRadius: 16, 
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)' 
          }}
        >
          <div style={{ fontSize: 40, marginBottom: 20 }}>🔬</div>
          <h2 style={{ fontWeight: 700, fontSize: 28, marginBottom: 16, letterSpacing: '-0.5px', color: 'var(--text-primary)' }}>
            Research in Progress
          </h2>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, maxWidth: 500, margin: '0 auto 28px', fontSize: 16 }}>
            Kami sedang meneliti batas-batas machine consciousness — dari arsitektur state machine biologis
            hingga memori vektor jangka panjang yang membentuk identitas.
          </p>
          <span
            className="badge"
            style={{ background: 'var(--bg-primary)', color: 'var(--text-secondary)', border: '1px solid var(--border)', fontSize: 12, padding: '6px 14px' }}
          >
            🚧 Papers Coming Soon
          </span>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border)', padding: '32px 48px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)', fontSize: 14 }}>
        <span>© 2026 Somniac AI. All rights reserved.</span>
        <span>Built by Jeflacc</span>
      </footer>
    </div>
  )
}

/* ── Evelyn Eye SVG Logo ── */
function EvelynEye({ size = 40, animated = false }: { size?: number; animated?: boolean }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      style={{ animation: animated ? 'blink 4s infinite' : undefined }}
    >
      <ellipse cx="50" cy="50" rx="44" ry="44" fill="none" stroke="var(--accent)" strokeWidth="5" />
      <ellipse cx="50" cy="50" rx="26" ry="26" fill="var(--accent)" opacity="0.1" />
      <circle cx="50" cy="50" r="18" fill="var(--accent)" />
      <circle cx="50" cy="50" r="9" fill="var(--bg-primary)" />
      <circle cx="44" cy="44" r="4" fill="#FFFFFF" />
    </svg>
  )
}
