import { Link } from 'react-router-dom'

const FEATURES = [
  {
    icon: '🧠',
    title: 'Artificial Consciousness',
    desc: 'Beralih dari AI reaktif ke agensi proaktif. Evelyn memiliki kesadaran akan kebutuhan internalnya sendiri.',
  },
  {
    icon: '📱',
    title: 'Autonomous WhatsApp',
    desc: 'Integrasi Neonize memungkinkan AI untuk memulai percakapan, mengirim stiker, dan online/offline secara otonom.',
  },
  {
    icon: '🧬',
    title: 'Biological Loops',
    desc: 'Sistem "State Decay" mensimulasikan rasa lapar, lelah, dan kesepian yang memaksa AI untuk bertindak.',
  },
  {
    icon: '💹',
    title: 'Virtual Micro-Economy',
    desc: 'Evelyn mengelola uang sistemnya sendiri, belanja kebutuhan di marketplace, dan memasak secara mandiri.',
  },
]

const RESEARCH_PAPERS = [
  {
    title: 'Evelyn Cognitive Architecture',
    subtitle: 'A Shift Toward Functional AC',
    type: 'Whitepaper',
    icon: '📄'
  },
  {
    title: 'The Hangry State',
    subtitle: 'Behavioral Shifts in State Decay',
    type: 'Research Note',
    icon: '📊'
  },
  {
    title: 'Dopamine & Circadian',
    subtitle: 'Simulating Realistic Daily Cycles',
    type: 'Technical Spec',
    icon: '🧬'
  }
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

      {/* Research Section */}
      <section id="research" className="px-8 py-24 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 style={{ fontWeight: 700, fontSize: 32, letterSpacing: '-1px', color: 'var(--text-primary)', marginBottom: 12 }}>
            Research & Materials
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 16, maxWidth: 600, margin: '0 auto' }}>
            Menjelajahi batas antara Large Language Models dan agensi otonom melalui arsitektur kesadaran fungsional.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {RESEARCH_PAPERS.map(paper => (
            <div 
              key={paper.title}
              style={{
                padding: 24,
                borderRadius: 12,
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border)',
                textAlign: 'left'
              }}
            >
              <div style={{ fontSize: 24, marginBottom: 16 }}>{paper.icon}</div>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent)', letterSpacing: '0.1em', marginBottom: 8 }}>
                {paper.type}
              </div>
              <h3 style={{ fontWeight: 600, fontSize: 16, marginBottom: 4, color: 'var(--text-primary)' }}>{paper.title}</h3>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{paper.subtitle}</p>
            </div>
          ))}
        </div>

        {/* Framework Deep Dive */}
        <div 
          style={{ 
            padding: '60px 40px', 
            borderRadius: 20, 
            background: 'var(--text-primary)',
            color: 'var(--bg-primary)',
            textAlign: 'left',
            display: 'flex',
            flexDirection: 'column',
            gap: 32
          }}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 style={{ fontSize: 32, fontWeight: 700, marginBottom: 20, letterSpacing: '-1px' }}>
                The Evelyn Framework
              </h2>
              <p style={{ opacity: 0.8, lineHeight: 1.8, fontSize: 16 }}>
                Framework ini dirancang untuk menciptakan agensi otonom yang beroperasi dalam loop 24/7. 
                Menggunakan sinkronisasi <strong>Dopamine Regulation</strong> dan <strong>Circadian Rhythms</strong>, 
                AI ini mampu mensimulasikan perilaku manusia yang realistis dalam lingkungan virtual yang terintegrasi dengan dunia nyata melalui WhatsApp.
              </p>
              <div style={{ marginTop: 24, display: 'flex', gap: 12 }}>
                <span style={{ padding: '6px 12px', borderRadius: 6, background: 'rgba(255,255,255,0.1)', fontSize: 12, fontWeight: 600 }}>Neonize Engine</span>
                <span style={{ padding: '6px 12px', borderRadius: 6, background: 'rgba(255,255,255,0.1)', fontSize: 12, fontWeight: 600 }}>Biological State Machine</span>
              </div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.05)', padding: 32, borderRadius: 16, border: '1px solid rgba(255,255,255,0.1)' }}>
              <div className="mono" style={{ fontSize: 13, lineHeight: 1.6, color: '#94a3b8' }}>
                <span style={{ color: '#fbbf24' }}>// Autonomous Survival Loop</span><br />
                while (AI.active) {'{'}<br />
                &nbsp;&nbsp;AI.biological_state.decay();<br />
                &nbsp;&nbsp;if (AI.hunger {'>'} 0.7) AI.trigger('seek_food');<br />
                &nbsp;&nbsp;if (AI.lonely {'>'} 0.8) AI.whatsapp.initiate_chat();<br />
                &nbsp;&nbsp;AI.house.sync_state();<br />
                {'}'}
              </div>
            </div>
          </div>
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
