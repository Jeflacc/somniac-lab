import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Link } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { useAIConnection, type Message, type AIState } from '../hooks/useAIConnection'

/* ── Helpers ──────────────────────────────────────────────────────────────── */

function StatBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100)
  return (
    <div>
      <div className="flex justify-between mb-1" style={{ fontSize: 12 }}>
        <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
        <span className="mono" style={{ color, fontSize: 11 }}>{pct}%</span>
      </div>
      <div className="stat-bar-track">
        <div className="stat-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

function MoodBadge({ mood }: { mood: string }) {
  const map: Record<string, { emoji: string; color: string; bg: string }> = {
    senang:  { emoji: '😊', color: '#34d399', bg: 'rgba(52,211,153,0.1)' },
    sedih:   { emoji: '😢', color: '#60a5fa', bg: 'rgba(96,165,250,0.1)' },
    marah:   { emoji: '😠', color: '#f87171', bg: 'rgba(248,113,113,0.1)' },
    netral:  { emoji: '😐', color: '#8888aa', bg: 'rgba(136,136,170,0.1)' },
  }
  const m = map[mood?.toLowerCase()] || map.netral
  return (
    <span
      className="badge"
      style={{ background: m.bg, color: m.color, border: `1px solid ${m.color}33` }}
    >
      {m.emoji} {mood || 'Netral'}
    </span>
  )
}

function HeartBeat({ bpm }: { bpm: number }) {
  return (
    <div className="flex items-center gap-1">
      <span style={{ color: '#f87171', fontSize: 14, animation: `pulse-glow 1s infinite` }}>♥</span>
      <span className="mono" style={{ fontSize: 13, color: '#f87171' }}>{bpm} bpm</span>
    </div>
  )
}

function ActivityBadge({ chore }: { chore: string | null }) {
  if (!chore) return <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Idle</span>
  const icons: Record<string, string> = {
    eat: '🍳', mandi: '🚿', sleep_routine: '😴', wake_routine: '🥱',
    play_console: '🎮', watch_tv: '📺', wander: '🚶', laundry: '👕',
    online_shopping: '🛒', check_wa: '📱',
  }
  return (
    <span className="badge" style={{ background: 'var(--accent-glow)', color: 'var(--accent)', border: '1px solid var(--accent-glow)', fontSize: 11 }}>
      {icons[chore] || '⚙️'} {chore.replace(/_/g, ' ')}
    </span>
  )
}

function EvelynEye({ size = 36, sleeping = false }: { size?: number; sleeping?: boolean }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100"
      style={{ animation: sleeping ? 'none' : 'blink 5s infinite', flexShrink: 0 }}>
      <ellipse cx="50" cy="50" rx="44" ry="44" fill="none" stroke="var(--accent)" strokeWidth="4" />
      <ellipse cx="50" cy="50" rx="26" ry="26" fill="var(--accent)" opacity="0.15" />
      {sleeping ? (
        <ellipse cx="50" cy="55" rx="18" ry="4" fill="var(--accent)" opacity="0.5" />
      ) : (
        <>
          <circle cx="50" cy="50" r="18" fill="var(--accent)" />
          <circle cx="50" cy="50" r="9" fill="var(--bg-primary)" />
          <circle cx="44" cy="44" r="4" fill="rgba(255,255,255,0.7)" />
        </>
      )}
    </svg>
  )
}

/* ── Chat Bubble ─────────────────────────────────────────────────────────── */
function ChatMessage({ msg }: { msg: Message }) {
  if (msg.role === 'system') {
    return (
      <div style={{ textAlign: 'center', padding: '4px 0' }}>
        <span className="badge" style={{ background: 'rgba(251,191,36,0.08)', color: '#fbbf24', fontSize: 11 }}>
          {msg.text}
        </span>
      </div>
    )
  }
  if (msg.role === 'user') {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <div className="chat-bubble-user">
          <p style={{ fontSize: 14, whiteSpace: 'pre-wrap' }}>{msg.text}</p>
        </div>
      </div>
    )
  }
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
      <EvelynEye size={28} />
      <div className="chat-bubble-ai">
        <p style={{ fontSize: 14, whiteSpace: 'pre-wrap' }}>{msg.text}</p>
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
      <EvelynEye size={28} />
      <div className="chat-bubble-ai" style={{ padding: '14px 18px' }}>
        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    </div>
  )
}

function StreamingBubble({ text }: { text: string }) {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
      <EvelynEye size={28} />
      <div className="chat-bubble-ai">
        <p style={{ fontSize: 14, whiteSpace: 'pre-wrap' }}>
          {text}
          <span style={{ display: 'inline-block', width: 2, height: 14, background: 'var(--accent)', marginLeft: 2, animation: 'typing 0.8s infinite', verticalAlign: 'middle' }} />
        </p>
      </div>
    </div>
  )
}

/* ── Right Sidebar: AC Dashboard ─────────────────────────────────────────── */
function ACDashboard({ aiState, houseState, economy, sendCommand }: {
  aiState:    AIState | null
  houseState: any
  economy:    any
  sendCommand: (cmd: string, payload?: string) => void
}) {
  if (!aiState) {
    return (
      <div style={{ padding: 20, color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', paddingTop: 40 }}>
        <div style={{ animation: 'spin 1s linear infinite', width: 20, height: 20, border: '2px solid var(--border)', borderTopColor: 'var(--accent)', borderRadius: '50%', margin: '0 auto 12px' }} />
        Connecting to engine...
      </div>
    )
  }

  return (
    <div style={{ padding: '16px 16px', display: 'flex', flexDirection: 'column', gap: 20, overflow: 'auto', flex: 1 }}>

      {/* Status */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <EvelynEye size={44} sleeping={aiState.is_sleeping} />
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>Evelyn</div>
            <MoodBadge mood={aiState.mood} />
          </div>
        </div>
        <HeartBeat bpm={aiState.heart_rate} />
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
          {aiState.breath_rate} breaths/min
        </div>
      </div>

      {/* Biology */}
      <div>
        <SectionTitle>Biology</SectionTitle>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 10 }}>
          <StatBar label="Hunger"     value={aiState.hunger}     color={barColor(aiState.hunger)} />
          <StatBar label="Sleepiness" value={aiState.sleepiness} color={barColor(aiState.sleepiness)} />
          <StatBar label="Libido"     value={aiState.libido}     color="var(--accent-2)" />
        </div>
      </div>

      {/* Current Activity */}
      <div>
        <SectionTitle>Activity</SectionTitle>
        <div style={{ marginTop: 8 }}>
          <ActivityBadge chore={houseState?.current_chore_id || null} />
          {houseState?.current_chore_label && (
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{houseState.current_chore_label}</p>
          )}
        </div>
      </div>

      {/* Relationship */}
      <div>
        <SectionTitle>Relationship</SectionTitle>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8, lineHeight: 1.5 }}>{aiState.relationship}</p>
      </div>

      {/* Economy */}
      {economy && (
        <div>
          <SectionTitle>Wallet</SectionTitle>
          <p className="mono" style={{ fontSize: 14, color: 'var(--green)', marginTop: 8 }}>
            {economy.formatted_balance || `Rp ${economy.balance?.toLocaleString('id-ID')}`}
          </p>
        </div>
      )}

      {/* Quick Commands */}
      <div>
        <SectionTitle>Quick Actions</SectionTitle>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 }}>
          <QuickBtn onClick={() => sendCommand('sleep')} icon="💤" label="Suruh Tidur" />
          <QuickBtn onClick={() => sendCommand('wake')}  icon="🥱" label="Bangunkan" />
          <QuickBtn onClick={() => sendCommand('feed', 'nasi goreng')} icon="🍳" label="Beri Makan" />
        </div>
      </div>

    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      textTransform: 'uppercase',
      fontSize: 10,
      fontWeight: 700,
      letterSpacing: '0.1em',
      color: 'var(--text-muted)',
      paddingBottom: 6,
      borderBottom: '1px solid var(--border)',
    }}>
      {children}
    </div>
  )
}

function QuickBtn({ onClick, icon, label }: { onClick: () => void; icon: string; label: string }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: 'var(--bg-primary)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: '8px 12px',
        color: 'var(--text-secondary)',
        fontSize: 12,
        fontWeight: 500,
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        textAlign: 'left',
        transition: 'all 0.15s',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--text-primary)'
        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-primary)'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-secondary)'
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border)'
        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-secondary)'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-primary)'
      }}
    >
      <span>{icon}</span> {label}
    </button>
  )
}

function barColor(v: number): string {
  if (v < 0.4) return 'var(--green)'
  if (v < 0.7) return 'var(--yellow)'
  return 'var(--red)'
}

/* ── Main Lab Page ───────────────────────────────────────────────────────── */
export default function LabPage() {
  const { connected, aiState, houseState, economy, messages, isThinking, streamBuffer, qrString, sendMessage, sendCommand, generateQr } = useAIConnection()
  const [input, setInput] = useState('')
  const [currentTab, setCurrentTab] = useState<'chat' | 'settings'>('chat')
  const [masterPhone, setMasterPhone] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef  = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking, streamBuffer])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isThinking) return
    sendMessage(text)
    setInput('')
    inputRef.current?.focus()
  }

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)' }}>

      {/* ── Left Sidebar ─────────────────────────────────────────────────── */}
      <aside style={{
        width: 220,
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        padding: '16px 12px',
        flexShrink: 0,
      }}>
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none', marginBottom: 24 }}>
          <EvelynEye size={26} sleeping={aiState?.is_sleeping} />
          <span style={{ fontWeight: 700, fontSize: 16, color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>somniac</span>
        </Link>

        {/* Connection status */}
        <div className="flex items-center gap-2 mb-6" style={{ fontSize: 12 }}>
          <span style={{
            width: 7, height: 7, borderRadius: '50%',
            background: connected ? 'var(--green)' : 'var(--red)',
            boxShadow: connected ? '0 0 6px var(--green)' : 'none',
            flexShrink: 0,
          }} />
          <span style={{ color: connected ? 'var(--green)' : 'var(--text-muted)' }}>
            {connected ? 'Engine Connected' : 'Reconnecting...'}
          </span>
        </div>

        {/* Nav */}
        <div style={{ marginBottom: 8, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', padding: '0 12px' }}>
          Navigation
        </div>
        <div 
          className={`sidebar-item ${currentTab === 'chat' ? 'active' : ''}`}
          onClick={() => setCurrentTab('chat')}
          style={{ cursor: 'pointer' }}
        >
          <span>💬</span> Chat
        </div>
        <div className="sidebar-item" style={{ marginTop: 2, opacity: 0.5, cursor: 'not-allowed' }}>
          <span>📓</span> Journal
        </div>
        <div 
          className={`sidebar-item ${currentTab === 'settings' ? 'active' : ''}`}
          onClick={() => setCurrentTab('settings')}
          style={{ cursor: 'pointer', marginTop: 2 }}
        >
          <span>⚙️</span> Settings
        </div>

        {/* AI info at bottom */}
        <div style={{ marginTop: 'auto', padding: '12px', background: 'var(--bg-card)', borderRadius: 10, border: '1px solid var(--border)' }}>
          {aiState && (
            <>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Evelyn</div>
              <MoodBadge mood={aiState.mood} />
            </>
          )}
        </div>
      </aside>

      {/* ── Center: Chat ─────────────────────────────────────────────────── */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header */}
        <div style={{
          height: 56,
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          gap: 12,
          flexShrink: 0,
        }}>
          <EvelynEye size={28} sleeping={aiState?.is_sleeping} />
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Evelyn</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              {aiState?.is_sleeping ? '💤 Sedang tidur' : 'Artificial Consciousness'}
            </div>
          </div>
          {aiState && <MoodBadge mood={aiState.mood} />}
        </div>

        {currentTab === 'chat' ? (
          <>
            {/* Messages */}
            <div style={{ flex: 1, overflow: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
              {messages.length === 0 && !isThinking && (
                <div style={{ textAlign: 'center', marginTop: 60, color: 'var(--text-muted)' }}>
                  <EvelynEye size={56} sleeping={aiState?.is_sleeping} />
                  <p style={{ marginTop: 16, fontSize: 15 }}>
                    {aiState?.is_sleeping ? 'Evelyn sedang tidur... 💤' : 'Mulai percakapan dengan Evelyn'}
                  </p>
                </div>
              )}

              {messages.map(msg => (
                <ChatMessage key={msg.id} msg={msg} />
              ))}

              {isThinking && streamBuffer && <StreamingBubble text={streamBuffer} />}
              {isThinking && !streamBuffer && <TypingIndicator />}

              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
              <div style={{ position: 'relative' }}>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder={aiState?.is_sleeping ? 'Evelyn sedang tidur...' : 'Ketik pesan (Enter untuk kirim, Shift+Enter baris baru)'}
                  disabled={aiState?.is_sleeping || isThinking}
                  rows={1}
                  className="chat-input"
                  style={{
                    maxHeight: 120,
                    overflowY: 'auto',
                    opacity: aiState?.is_sleeping ? 0.5 : 1,
                  }}
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isThinking || aiState?.is_sleeping}
                  style={{
                    position: 'absolute',
                    right: 12,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: !input.trim() || isThinking ? 'var(--border)' : 'var(--text-primary)',
                    border: 'none',
                    borderRadius: 8,
                    padding: '6px 12px',
                    cursor: !input.trim() || isThinking ? 'default' : 'pointer',
                    color: 'var(--bg-primary)',
                    fontSize: 16,
                    fontWeight: 600,
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={e => {
                    if (input.trim() && !isThinking) e.currentTarget.style.background = 'var(--accent-2)'
                  }}
                  onMouseLeave={e => {
                    if (input.trim() && !isThinking) e.currentTarget.style.background = 'var(--text-primary)'
                  }}
                >
                  {isThinking ? '⏳' : '↑'}
                </button>
              </div>
              <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 6, textAlign: 'center' }}>
                Somniac AI · Artificial Consciousness Engine
              </p>
            </div>
          </>
        ) : (
          <div style={{ padding: 40, flex: 1, overflow: 'auto' }}>
            <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 20 }}>Settings</h2>
            
            <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 12, border: '1px solid var(--border)' }}>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#25D366' }}>📱</span> WhatsApp Multi-Tenant Connection
              </h3>
              <p style={{ marginBottom: 16, color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.5 }}>
                Connect Evelyn to your personal WhatsApp number. This is an isolated session tied only to your account.
              </p>
              
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', marginBottom: 8, fontSize: 13, fontWeight: 600 }}>Master Phone Number</label>
                <input 
                  type="text" 
                  value={masterPhone}
                  onChange={e => setMasterPhone(e.target.value)}
                  placeholder="e.g. 628123456789"
                  style={{
                    width: '100%',
                    maxWidth: 300,
                    padding: '10px 14px',
                    borderRadius: 8,
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border)',
                    color: 'var(--text-primary)',
                  }}
                />
              </div>
              
              <button 
                onClick={() => generateQr(masterPhone)}
                style={{
                  background: 'var(--text-primary)',
                  color: 'var(--bg-primary)',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: 8,
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--accent-2)'}
                onMouseLeave={e => e.currentTarget.style.background = 'var(--text-primary)'}
              >
                Generate Connection QR
              </button>
              
              {qrString && (
                <div style={{ marginTop: 30, padding: 20, background: 'var(--bg-primary)', borderRadius: 12, border: '1px solid var(--border)', display: 'inline-block' }}>
                  {qrString === 'LOADING' ? (
                    <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)' }}>
                      Loading WhatsApp Session...
                    </div>
                  ) : qrString === 'CONNECTED' ? (
                    <div style={{ textAlign: 'center', padding: 20, color: 'var(--green)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: 24 }}>🟢</span> Connected to WhatsApp!
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center' }}>
                      <p style={{ marginBottom: 16, fontSize: 13, color: 'var(--text-secondary)' }}>Scan this QR code with WhatsApp Linked Devices</p>
                      <div style={{ background: 'white', padding: 16, borderRadius: 8, display: 'inline-block' }}>
                        <QRCodeSVG value={qrString} size={200} />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* ── Right Sidebar: AC Dashboard ──────────────────────────────────── */}
      <aside style={{
        width: 260,
        background: 'var(--bg-secondary)',
        borderLeft: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        overflow: 'hidden',
      }}>
        <div style={{ padding: '16px 16px 12px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
          <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', fontWeight: 700 }}>
            AC Dashboard
          </div>
        </div>
        <ACDashboard aiState={aiState} houseState={houseState} economy={economy} sendCommand={sendCommand} />
      </aside>

    </div>
  )
}
