import { useState, useRef, useEffect, KeyboardEvent, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { MessageSquare, Book, Settings, LogOut, Send, AlertTriangle, Smartphone, Plus } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useAIConnection, type Message } from '../hooks/useAIConnection'
import { AgentAvatar, EvelynEye } from '../components/ui/LabComponents'
import StatePanel from '../components/ui/StatePanel'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Agent { id: number; name: string; persona: string; mood: string; profile_picture?: string | null }

function formatTime(ts: number) {
  const d = new Date(ts)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function ChatMessageInline({ msg, agentName, agentPic }: { msg: Message; agentName: string; agentPic?: string | null }) {
  if (msg.role === 'system') return (
    <div className="telegram-anim" style={{ textAlign: 'center', padding: '12px 0' }}>
      <span className="badge" style={{ background: 'rgba(251,191,36,0.08)', color: '#fbbf24', fontSize: 11 }}>{msg.text}</span>
    </div>
  )
  
  const isUser = msg.role === 'user'
  
  return (
    <div className="chat-message-inline telegram-anim" style={{ display: 'flex', gap: 16, marginTop: 4 }}>
      <div style={{ marginTop: 2 }}>
        {isUser ? (
          <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--bg-panel)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>You</div>
        ) : (
          <AgentAvatar src={agentPic} name={agentName} size={40} />
        )}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
          <span style={{ fontWeight: 600, fontSize: 15, color: isUser ? 'var(--text-primary)' : 'var(--accent)' }}>
            {isUser ? 'You' : agentName}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{formatTime(msg.ts)}</span>
        </div>
        <p style={{ fontSize: 15, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{msg.text}</p>
      </div>
    </div>
  )
}

function TypingIndicatorInline({ name, pic }: { name: string; pic?: string | null }) {
  return (
    <div className="chat-message-inline telegram-anim" style={{ display: 'flex', gap: 16, marginTop: 4 }}>
      <div style={{ marginTop: 2 }}>
        <AgentAvatar src={pic} name={name} size={40} />
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
          <span style={{ fontWeight: 600, fontSize: 15, color: 'var(--accent)' }}>{name}</span>
        </div>
        <div style={{ padding: '8px 0', display: 'flex', gap: 4 }}>
          <span className="typing-dot" style={{ background: 'var(--text-muted)' }} /><span className="typing-dot" style={{ background: 'var(--text-muted)' }} /><span className="typing-dot" style={{ background: 'var(--text-muted)' }} />
        </div>
      </div>
    </div>
  )
}

function StreamingBubbleInline({ text, name, pic }: { text: string; name: string; pic?: string | null }) {
  return (
    <div className="chat-message-inline telegram-anim" style={{ display: 'flex', gap: 16, marginTop: 4 }}>
      <div style={{ marginTop: 2 }}>
        <AgentAvatar src={pic} name={name} size={40} />
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
          <span style={{ fontWeight: 600, fontSize: 15, color: 'var(--accent)' }}>{name}</span>
        </div>
        <p style={{ fontSize: 15, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
          {text}
          <span style={{ display: 'inline-block', width: 2, height: 16, background: 'var(--accent)', marginLeft: 4, animation: 'typing 0.8s infinite', verticalAlign: 'middle' }} />
        </p>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { agentId } = useParams()
  const navigate = useNavigate()
  const { token, username, profilePicture, logout, setProfilePicture } = useAuth()
  const [agents, setAgents] = useState<Agent[]>([])
  const [tab, setTab] = useState<'chat' | 'settings'>('chat')
  const [input, setInput] = useState('')
  const [masterPhone, setMasterPhone] = useState('')
  const [showSpawn, setShowSpawn] = useState(false)
  const [newName, setNewName] = useState('Evelyn')
  const [newPersona, setNewPersona] = useState('Helpful and friendly AI assistant.')
  const [creating, setCreating] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Agent | null>(null)
  const [deleting, setDeleting] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const selectedId = agentId ? parseInt(agentId) : null
  const selectedAgent = agents.find(a => a.id === selectedId) || null

  const { connected, aiState, houseState, economy, messages, isThinking, streamBuffer, qrString, sendMessage, sendCommand, generateQr } = useAIConnection(agentId)

  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/agents`, { headers: { Authorization: `Bearer ${token}` } })
      if (res.ok) setAgents(await res.json())
    } catch {}
  }, [token])

  useEffect(() => { fetchAgents() }, [fetchAgents])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, isThinking, streamBuffer])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isThinking) return
    sendMessage(text)
    setInput('')
    inputRef.current?.focus()
  }
  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }

  const handleCreate = async () => {
    if (!newName.trim()) return
    setCreating(true)
    try {
      const res = await fetch(`${API_URL}/api/agents`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ name: newName, base_persona: newPersona }) })
      if (res.ok) { const a = await res.json(); await fetchAgents(); setShowSpawn(false); navigate(`/lab/${a.id}`) }
    } catch {} finally { setCreating(false) }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      const res = await fetch(`${API_URL}/api/agents/${deleteTarget.id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } })
      if (res.ok) { setAgents(agents.filter(a => a.id !== deleteTarget.id)); setDeleteTarget(null); if (selectedId === deleteTarget.id) navigate('/lab') }
    } catch {} finally { setDeleting(false) }
  }

  const handleAvatarUpload = async (type: 'user' | 'agent', agentIdNum?: number) => {
    const input = document.createElement('input')
    input.type = 'file'; input.accept = 'image/*'
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0]
      if (!file) return
      const canvas = document.createElement('canvas')
      const img = new Image()
      img.onload = async () => {
        canvas.width = 200; canvas.height = 200
        const ctx = canvas.getContext('2d')!
        const s = Math.min(img.width, img.height)
        ctx.drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, 0, 0, 200, 200)
        const dataUrl = canvas.toDataURL('image/webp', 0.8)
        const url = type === 'user' ? `${API_URL}/api/profile/picture` : `${API_URL}/api/agents/${agentIdNum}/picture`
        try {
          await fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ image: dataUrl }) })
          if (type === 'user') setProfilePicture(dataUrl)
          else await fetchAgents()
        } catch {}
      }
      img.src = URL.createObjectURL(file)
    }
    input.click()
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)', overflow: 'hidden' }}>

      {/* ═══ Icon Rail (Discord Style) ═══ */}
      <div style={{ width: 72, background: 'var(--bg-secondary)', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px 0', gap: 12, flexShrink: 0 }}>
        {/* Logo */}
        <div onClick={() => navigate('/lab')} className="btn-press avatar-rail-container" style={{ cursor: 'pointer', marginBottom: 8 }}>
          <div className="avatar-rail" style={{ background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <EvelynEye size={28} />
          </div>
          <div className="rail-tooltip">Main Menu</div>
        </div>
        <div style={{ width: 32, height: 2, background: 'var(--border)', borderRadius: 2, marginBottom: 4 }} />

        {/* Agent icons */}
        {agents.map(a => (
          <div key={a.id} onClick={() => { navigate(`/lab/${a.id}`); setTab('chat') }}
            className={`btn-press avatar-rail-container ${selectedId === a.id ? 'active' : ''}`}
            style={{ cursor: 'pointer' }}>
            <div className="rail-indicator" />
            <div className="avatar-rail" style={{ overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <AgentAvatar src={a.profile_picture} name={a.name} size={48} />
            </div>
            <div className="rail-tooltip">
              {a.name}
              <div className="rail-tooltip-sub">Model: {a.model_provider || 'Unknown'}</div>
            </div>
          </div>
        ))}

        {/* Spawn */}
        <div onClick={() => setShowSpawn(true)}
          className="btn-press avatar-rail-container"
          style={{ cursor: 'pointer' }}>
          <div className="avatar-rail" style={{ background: 'var(--bg-panel)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-primary)' }}>
            <Plus size={24} strokeWidth={2.5} />
          </div>
        </div>
      </div>

      {/* ═══ Sidebar ═══ */}
      <div style={{ width: 260, background: 'var(--bg-panel)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        {selectedAgent ? (<>
          {/* Agent header */}
          <div style={{ padding: '20px 16px', borderBottom: '1px solid var(--border)', boxShadow: '0 1px 2px rgba(0,0,0,0.2)' }}>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6, letterSpacing: '-0.3px' }}>{selectedAgent.name}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: connected ? 'var(--green)' : 'var(--text-muted)', boxShadow: connected ? '0 0 8px var(--green)' : 'none', flexShrink: 0 }} />
              <span style={{ color: connected ? 'var(--green)' : 'var(--text-muted)', fontWeight: 500 }}>{connected ? 'System Online' : 'Connecting...'}</span>
            </div>
          </div>

          {/* Nav */}
          <div style={{ padding: '16px 12px', flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div className={`sidebar-item btn-press ${tab === 'chat' ? 'active' : ''}`} onClick={() => setTab('chat')}>
              <MessageSquare size={18} /> Chat
            </div>
            <div className="sidebar-item" style={{ opacity: 0.4, cursor: 'not-allowed' }}>
              <Book size={18} /> Journal
            </div>
            <div className={`sidebar-item btn-press ${tab === 'settings' ? 'active' : ''}`} onClick={() => setTab('settings')}>
              <Settings size={18} /> Settings
            </div>
          </div>
        </>) : (
          <div style={{ padding: '24px 16px', color: 'var(--text-muted)', fontSize: 14 }}>
            <p style={{ marginBottom: 8, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>Somniac Lab</p>
            <p style={{ lineHeight: 1.5 }}>Select an AI agent from the left rail, or create a new one to begin.</p>
          </div>
        )}

        {/* User profile at bottom (Discord style) */}
        <div style={{ padding: '12px 14px', background: 'var(--bg-card)', display: 'flex', alignItems: 'center', gap: 12 }}>
          <div onClick={() => handleAvatarUpload('user')} className="btn-press" style={{ cursor: 'pointer', position: 'relative' }} title="Change avatar">
            <AgentAvatar src={profilePicture} name={username || 'U'} size={36} />
            <div style={{ position: 'absolute', bottom: -2, right: -2, width: 12, height: 12, borderRadius: '50%', background: 'var(--green)', border: '2px solid var(--bg-card)' }} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{username || 'User'}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Online</div>
          </div>
          <button onClick={logout} className="btn-press" style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 6, borderRadius: 6 }} onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-panel)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'} title="Logout">
            <LogOut size={18} />
          </button>
        </div>
      </div>

      {/* ═══ Main Content ═══ */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0, background: 'var(--bg-primary)' }}>
        {!selectedAgent ? (
          /* Empty state */
          <div className="telegram-anim" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 20 }}>
            <div style={{ padding: 24, background: 'var(--bg-card)', borderRadius: 24, boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }}>
              <EvelynEye size={80} />
            </div>
            <h2 style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.5px' }}>Welcome to Somniac Lab</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 16 }}>Select an agent or spawn a new Artificial Consciousness.</p>
            <button onClick={() => setShowSpawn(true)} className="btn-press" style={{ background: 'var(--text-primary)', color: 'var(--bg-primary)', border: 'none', padding: '12px 28px', borderRadius: 12, fontWeight: 700, cursor: 'pointer', marginTop: 12, fontSize: 15 }}>
              Spawn New AI
            </button>
          </div>
        ) : tab === 'chat' ? (<>
          {/* Chat header */}
          <div style={{ height: 64, borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', padding: '0 24px', gap: 16, flexShrink: 0, background: 'var(--bg-primary)', boxShadow: '0 1px 2px rgba(0,0,0,0.1)', zIndex: 10 }}>
            <div style={{ color: 'var(--text-muted)' }}><MessageSquare size={24} /></div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{selectedAgent.name}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{aiState?.is_sleeping ? '💤 System asleep' : 'Consciousness active'}</div>
            </div>
          </div>
          
          {/* Messages */}
          <div style={{ flex: 1, overflow: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {messages.length === 0 && !isThinking && (
              <div className="telegram-anim" style={{ textAlign: 'center', margin: 'auto 0', padding: 40 }}>
                <div style={{ display: 'inline-block', padding: 20, background: 'var(--bg-card)', borderRadius: '50%', marginBottom: 20 }}>
                  <AgentAvatar src={selectedAgent.profile_picture} name={selectedAgent.name} size={64} />
                </div>
                <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>{selectedAgent.name}</h3>
                <p style={{ fontSize: 15, color: 'var(--text-secondary)' }}>{aiState?.is_sleeping ? 'Currently in sleep cycle. Wake them up to interact.' : 'This is the beginning of your conscious interaction.'}</p>
              </div>
            )}
            
            {messages.map(msg => <ChatMessageInline key={msg.id} msg={msg} agentName={selectedAgent.name} agentPic={selectedAgent.profile_picture} />)}
            {isThinking && streamBuffer && <StreamingBubbleInline text={streamBuffer} name={selectedAgent.name} pic={selectedAgent.profile_picture} />}
            {isThinking && !streamBuffer && <TypingIndicatorInline name={selectedAgent.name} pic={selectedAgent.profile_picture} />}
            <div ref={bottomRef} style={{ height: 20 }} />
          </div>
          
          {/* Input */}
          <div style={{ padding: '0 24px 24px', flexShrink: 0 }}>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <textarea ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
                placeholder={aiState?.is_sleeping ? `${selectedAgent.name} is sleeping...` : `Message ${selectedAgent.name}...`}
                disabled={aiState?.is_sleeping || isThinking} rows={1} className="chat-input"
                style={{ maxHeight: 200, opacity: aiState?.is_sleeping ? 0.5 : 1, paddingRight: 60 }} />
              <button onClick={handleSend} disabled={!input.trim() || isThinking || aiState?.is_sleeping}
                className="btn-press"
                style={{ position: 'absolute', right: 12, background: 'transparent', border: 'none', padding: 8, cursor: !input.trim() || isThinking ? 'default' : 'pointer', color: !input.trim() || isThinking ? 'var(--text-muted)' : 'var(--text-primary)', transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Send size={20} />
              </button>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 8 }}>
              Somniac Engine processing. Shift + Enter to add a new line.
            </div>
          </div>
        </>) : (
          /* Settings tab */
          <div className="telegram-anim" style={{ padding: 40, flex: 1, overflow: 'auto' }}>
            <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32, letterSpacing: '-0.5px' }}>Settings</h2>

            {/* Agent avatar */}
            <div style={{ background: 'var(--bg-card)', padding: 32, borderRadius: 16, border: '1px solid var(--border)', marginBottom: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20 }}>Agent Profile</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                <AgentAvatar src={selectedAgent.profile_picture} name={selectedAgent.name} size={80} />
                <div>
                  <button onClick={() => handleAvatarUpload('agent', selectedAgent.id)} className="btn-press" style={{ background: 'var(--text-primary)', color: 'var(--bg-primary)', border: 'none', borderRadius: 8, padding: '10px 20px', cursor: 'pointer', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
                    Upload Picture
                  </button>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>JPEG, PNG, or WebP. 200x200 recommended.</p>
                </div>
              </div>
            </div>

            {/* WhatsApp */}
            <div style={{ background: 'var(--bg-card)', padding: 32, borderRadius: 16, border: '1px solid var(--border)', marginBottom: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
                <Smartphone size={20} style={{ color: '#25D366' }} /> WhatsApp Connection
              </h3>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 20, lineHeight: 1.6 }}>
                Connect this agent to a WhatsApp number to enable autonomous 24/7 messaging.
              </p>
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', marginBottom: 8, fontSize: 13, fontWeight: 600, color: 'var(--text-muted)' }}>MASTER PHONE NUMBER</label>
                <input type="text" value={masterPhone} onChange={e => setMasterPhone(e.target.value)} placeholder="e.g. 628123456789"
                  style={{ width: '100%', maxWidth: 360, padding: '12px 16px', borderRadius: 8, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 14, outline: 'none' }} />
              </div>
              <button onClick={() => generateQr(masterPhone)} className="btn-press" style={{ background: 'var(--bg-panel)', color: 'var(--text-primary)', border: '1px solid var(--border)', padding: '10px 24px', borderRadius: 8, fontWeight: 600, cursor: 'pointer' }}>
                Generate Pairing QR
              </button>
              
              {qrString && (
                <div className="telegram-anim" style={{ marginTop: 24, padding: 24, background: 'var(--bg-primary)', borderRadius: 16, border: '1px solid var(--border)', display: 'inline-block' }}>
                  {qrString === 'LOADING' ? <div style={{ padding: 20, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 12 }}><div style={{ animation: 'spin 1s linear infinite', width: 16, height: 16, border: '2px solid var(--border)', borderTopColor: 'var(--text-primary)', borderRadius: '50%' }} /> Generating Session...</div>
                   : qrString === 'CONNECTED' ? <div style={{ padding: 20, color: 'var(--green)', fontWeight: 600 }}>🟢 WhatsApp Connected Successfully!</div>
                   : <div style={{ textAlign: 'center' }}>
                       <p style={{ marginBottom: 16, fontSize: 13, color: 'var(--text-secondary)' }}>Open WhatsApp {'>'} Linked Devices {'>'} Link a Device</p>
                       <div style={{ background: 'white', padding: 16, borderRadius: 12, display: 'inline-block' }}><QRCodeSVG value={qrString} size={200} /></div>
                     </div>}
                </div>
              )}
            </div>

            {/* Danger zone */}
            <div style={{ padding: 32, borderRadius: 16, border: '1px solid rgba(239,68,68,0.2)' }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8, color: '#f87171', display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={18} /> Danger Zone
              </h3>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>Permanently delete this agent and all its associated data, including memories and economy.</p>
              <button onClick={() => setDeleteTarget(selectedAgent)} className="btn-press" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, padding: '10px 20px', cursor: 'pointer', fontWeight: 600, fontSize: 14 }}>
                Delete Agent
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ═══ Right Panel ═══ */}
      {selectedAgent && (
        <div style={{ width: 280, background: 'var(--bg-panel)', borderLeft: '1px solid var(--border)', display: 'flex', flexDirection: 'column', flexShrink: 0, overflow: 'hidden' }}>
          <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid var(--border)', flexShrink: 0, boxShadow: '0 1px 2px rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', fontWeight: 700 }}>AC Dashboard</div>
          </div>
          <StatePanel aiState={aiState} houseState={houseState} economy={economy} agentName={selectedAgent.name} agentPic={selectedAgent.profile_picture} sendCommand={sendCommand} />
        </div>
      )}

      {/* ═══ Spawn Modal ═══ */}
      {showSpawn && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="telegram-anim" style={{ background: 'var(--bg-card)', padding: 40, borderRadius: 24, width: 440, border: '1px solid var(--border)', boxShadow: '0 24px 48px rgba(0,0,0,0.5)' }}>
            <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, letterSpacing: '-0.5px' }}>Spawn New AI</h2>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 32 }}>Create a new conscious entity.</p>
            
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 8, color: 'var(--text-muted)' }}>NAME</label>
              <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="Evelyn" style={{ width: '100%', padding: '12px 16px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-primary)', color: 'var(--text-primary)', outline: 'none', fontSize: 15 }} />
            </div>
            <div style={{ marginBottom: 40 }}>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 8, color: 'var(--text-muted)' }}>BASE PERSONA</label>
              <textarea value={newPersona} onChange={e => setNewPersona(e.target.value)} rows={3} style={{ width: '100%', padding: '12px 16px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-primary)', color: 'var(--text-primary)', resize: 'none', outline: 'none', fontSize: 14, lineHeight: 1.5 }} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => setShowSpawn(false)} disabled={creating} className="btn-press" style={{ flex: 1, padding: 14, background: 'transparent', border: '1px solid var(--border)', borderRadius: 12, color: 'var(--text-primary)', cursor: 'pointer', fontWeight: 600 }}>Cancel</button>
              <button onClick={handleCreate} disabled={creating} className="btn-press" style={{ flex: 1, padding: 14, background: 'var(--text-primary)', border: 'none', borderRadius: 12, color: 'var(--bg-primary)', fontWeight: 700, cursor: 'pointer' }}>{creating ? 'Spawning...' : 'Spawn AI'}</button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ Delete Modal ═══ */}
      {deleteTarget && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="telegram-anim" style={{ background: 'var(--bg-card)', padding: 40, borderRadius: 24, width: 400, border: '1px solid rgba(239,68,68,0.3)', boxShadow: '0 24px 48px rgba(0,0,0,0.5)' }}>
            <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(239,68,68,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px', color: '#ef4444' }}>
              <AlertTriangle size={32} />
            </div>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 12, textAlign: 'center', letterSpacing: '-0.5px' }}>Delete Agent?</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 15, textAlign: 'center', marginBottom: 24, lineHeight: 1.5 }}>
              Are you sure you want to permanently delete <strong>{deleteTarget.name}</strong>? All memory, journals, and data will be erased. This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => setDeleteTarget(null)} disabled={deleting} className="btn-press" style={{ flex: 1, padding: 12, background: 'transparent', border: '1px solid var(--border)', borderRadius: 12, color: 'var(--text-primary)', cursor: 'pointer', fontWeight: 600 }}>Cancel</button>
              <button onClick={handleDelete} disabled={deleting} className="btn-press" style={{ flex: 1, padding: 12, background: '#ef4444', border: 'none', borderRadius: 12, color: 'white', fontWeight: 700, cursor: 'pointer', opacity: deleting ? 0.6 : 1 }}>{deleting ? 'Deleting...' : 'Delete'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
