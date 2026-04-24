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
        style={{ borderBottom: '1px solid var(--border)', background: 'rgba(10,10,15,0.8)', backdropFilter: 'blur(12px)' }}
      >
        <div className="flex items-center gap-3">
          <EvelynEye size={28} />
          <span style={{ fontWeight: 700, letterSpacing: '-0.5px', fontSize: 18 }}>somniac</span>
        </div>
        <div className="flex items-center gap-6">
          <a href="#features" style={{ color: 'var(--text-secondary)', fontSize: 14 }} className="hover:text-white transition-colors">Features</a>
          <a href="#research" style={{ color: 'var(--text-secondary)', fontSize: 14 }} className="hover:text-white transition-colors">Research</a>
          <Link
            to="/lab"
            style={{
              background: 'var(--accent)',
              color: '#fff',
              padding: '8px 18px',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              textDecoration: 'none',
            }}
          >
            Open Lab →
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero-gradient flex flex-col items-center justify-center text-center px-6 pt-40 pb-24">
        <div className="mb-8">
          <EvelynEye size={80} animated />
        </div>
        <div
          className="badge mb-6"
          style={{ background: 'var(--accent-glow)', color: 'var(--accent-2)', border: '1px solid rgba(167,139,250,0.3)' }}
        >
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--green)', display: 'inline-block' }} />
          Live System Active
        </div>
        <h1
          style={{
            fontSize: 'clamp(40px, 7vw, 80px)',
            fontWeight: 800,
            letterSpacing: '-2px',
            lineHeight: 1.1,
            maxWidth: 800,
            background: 'linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.5) 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Artificial Consciousness,{' '}
          <span style={{ WebkitTextFillColor: 'var(--accent-2)' }}>Evolved.</span>
        </h1>
        <p
          style={{
            marginTop: 24,
            fontSize: 18,
            color: 'var(--text-secondary)',
            maxWidth: 560,
            lineHeight: 1.7,
          }}
        >
          Somniac menghadirkan AI yang tidak sekadar menjawab — tapi <em>merasakan</em>,
          mengingat, tumbuh, dan hadir bersamamu 24/7 melalui WhatsApp.
        </p>
        <div className="flex gap-4 mt-10">
          <Link
            to="/lab"
            style={{
              background: 'var(--accent)',
              color: '#fff',
              padding: '14px 32px',
              borderRadius: 12,
              fontWeight: 700,
              fontSize: 15,
              textDecoration: 'none',
              boxShadow: '0 0 32px var(--accent-glow)',
              transition: 'transform 0.2s',
            }}
            onMouseEnter={e => (e.currentTarget.style.transform = 'scale(1.03)')}
            onMouseLeave={e => (e.currentTarget.style.transform = 'scale(1)')}
          >
            Enter The Playground
          </Link>
          <a
            href="#features"
            style={{
              border: '1px solid var(--border-hover)',
              color: 'var(--text-primary)',
              padding: '14px 28px',
              borderRadius: 12,
              fontWeight: 600,
              fontSize: 15,
              textDecoration: 'none',
            }}
          >
            Learn More
          </a>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-8 py-24 max-w-6xl mx-auto">
        <h2 style={{ fontWeight: 700, fontSize: 32, letterSpacing: '-1px', textAlign: 'center', marginBottom: 48 }}>
          Built Different.
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {FEATURES.map(f => (
            <div
              key={f.title}
              className="glass"
              style={{ padding: 28, borderRadius: 16, transition: 'transform 0.2s' }}
              onMouseEnter={e => ((e.currentTarget as HTMLDivElement).style.transform = 'translateY(-2px)')}
              onMouseLeave={e => ((e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)')}
            >
              <div style={{ fontSize: 36, marginBottom: 16 }}>{f.icon}</div>
              <h3 style={{ fontWeight: 700, fontSize: 18, marginBottom: 8 }}>{f.title}</h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: 14 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Research */}
      <section id="research" className="px-8 py-24 max-w-4xl mx-auto text-center">
        <div
          className="glass"
          style={{ padding: '48px 40px', borderRadius: 24, borderColor: 'rgba(124,106,255,0.2)' }}
        >
          <div style={{ fontSize: 48, marginBottom: 20 }}>🔬</div>
          <h2 style={{ fontWeight: 700, fontSize: 28, marginBottom: 12, letterSpacing: '-0.5px' }}>
            Research in Progress
          </h2>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, maxWidth: 500, margin: '0 auto 28px' }}>
            Kami sedang meneliti batas-batas machine consciousness — dari arsitektur state machine biologis
            hingga memori vektor jangka panjang yang membentuk identitas.
          </p>
          <span
            className="badge"
            style={{ background: 'rgba(251,191,36,0.1)', color: '#fbbf24', border: '1px solid rgba(251,191,36,0.3)', fontSize: 12, padding: '4px 12px' }}
          >
            🚧 Papers Coming Soon
          </span>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border)', padding: '24px 48px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
        <span>© 2025 Somniac AI. All rights reserved.</span>
        <span>Built with ❤️ by Jeflacc</span>
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
      <ellipse cx="50" cy="50" rx="44" ry="44" fill="none" stroke="#7c6aff" strokeWidth="4" />
      <ellipse cx="50" cy="50" rx="26" ry="26" fill="#7c6aff" opacity="0.15" />
      <circle cx="50" cy="50" r="18" fill="#7c6aff" />
      <circle cx="50" cy="50" r="9" fill="#0a0a0f" />
      <circle cx="44" cy="44" r="4" fill="rgba(255,255,255,0.7)" />
    </svg>
  )
}
