import { useState, useRef, useEffect, KeyboardEvent, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { useAuth } from '../contexts/AuthContext'
import { useAIConnection, type Message } from '../hooks/useAIConnection'
import { AgentAvatar, MoodBadge, EvelynEye } from '../components/ui/LabComponents'
import StatePanel from '../components/ui/StatePanel'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Agent { id: number; name: string; persona: string; mood: string; profile_picture?: string | null }

function ChatMessage({ msg, agentName, agentPic }: { msg: Message; agentName: string; agentPic?: string | null }) {
  if (msg.role === 'system') return (
    <div style={{ textAlign: 'center', padding: '4px 0' }}>
      <span className="badge" style={{ background: 'rgba(251,191,36,0.08)', color: '#fbbf24', fontSize: 11 }}>{msg.text}</span>
    </div>
  )
  if (msg.role === 'user') return (
    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
      <div className="chat-bubble-user"><p style={{ fontSize: 14, whiteSpace: 'pre-wrap' }}>{msg.text}</p></div>
    </div>
  )
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
      <AgentAvatar src={agentPic} name={agentName} size={28} />
      <div className="chat-bubble-ai"><p style={{ fontSize: 14, whiteSpace: 'pre-wrap' }}>{msg.text}</p></div>
    </div>
  )
}

function TypingIndicator({ name, pic }: { name: string; pic?: string | null }) {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
      <AgentAvatar src={pic} name={name} size={28} />
      <div className="chat-bubble-ai" style={{ padding: '14px 18px' }}>
        <div style={{ display: 'flex', gap: 4 }}><span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" /></div>
      </div>
    </div>
  )
}

function StreamingBubble({ text, name, pic }: { text: string; name: string; pic?: string | null }) {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
      <AgentAvatar src={pic} name={name} size={28} />
      <div className="chat-bubble-ai">
        <p style={{ fontSize: 14, whiteSpace: 'pre-wrap' }}>{text}<span style={{ display: 'inline-block', width: 2, height: 14, background: 'var(--accent)', marginLeft: 2, animation: 'typing 0.8s infinite', verticalAlign: 'middle' }} /></p>
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

      {/* ═══ Icon Rail ═══ */}
      <div style={{ width: 72, background: 'var(--bg-secondary)', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '12px 0', gap: 8, flexShrink: 0 }}>
        {/* Logo */}
        <div onClick={() => navigate('/')} style={{ cursor: 'pointer', marginBottom: 8 }}>
          <EvelynEye size={32} />
        </div>
        <div style={{ width: 32, height: 1, background: 'var(--border)', marginBottom: 4 }} />

        {/* Agent icons */}
        {agents.map(a => (
          <div key={a.id} onClick={() => { navigate(`/lab/${a.id}`); setTab('chat') }}
            title={a.name}
            style={{ position: 'relative', cursor: 'pointer' }}>
            <div className={`avatar-rail ${selectedId === a.id ? 'active' : ''}`} style={{ overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <AgentAvatar src={a.profile_picture} name={a.name} size={44} />
            </div>
          </div>
        ))}

        {/* Spawn */}
        <div onClick={() => setShowSpawn(true)}
          style={{ width: 48, height: 48, borderRadius: 16, border: '2px dashed var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-muted)', fontSize: 22, transition: 'all 0.2s' }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--accent)' }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-muted)' }}
        >+</div>
      </div>

      {/* ═══ Sidebar ═══ */}
      <div style={{ width: 240, background: 'var(--bg-panel)', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        {selectedAgent ? (<>
          {/* Agent header */}
          <div style={{ padding: '16px 14px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{selectedAgent.name}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: connected ? 'var(--green)' : 'var(--red)', boxShadow: connected ? '0 0 6px var(--green)' : 'none', flexShrink: 0 }} />
              <span style={{ color: connected ? 'var(--green)' : 'var(--text-muted)' }}>{connected ? 'Connected' : 'Reconnecting...'}</span>
            </div>
          </div>

          {/* Nav */}
          <div style={{ padding: '12px 10px', flex: 1 }}>
            <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', padding: '0 12px', marginBottom: 6 }}>Navigation</div>
            <div className={`sidebar-item ${tab === 'chat' ? 'active' : ''}`} onClick={() => setTab('chat')}>💬 Chat</div>
            <div className="sidebar-item" style={{ opacity: 0.4, cursor: 'not-allowed', marginTop: 2 }}>📓 Journal</div>
            <div className={`sidebar-item ${tab === 'settings' ? 'active' : ''}`} onClick={() => setTab('settings')} style={{ marginTop: 2 }}>⚙️ Settings</div>
          </div>
        </>) : (
          <div style={{ padding: '20px 14px', color: 'var(--text-muted)', fontSize: 13 }}>
            <p style={{ marginBottom: 8, fontWeight: 600, color: 'var(--text-secondary)' }}>Somniac Lab</p>
            <p>Select an AI agent from the left rail, or create a new one.</p>
          </div>
        )}

        {/* User profile at bottom */}
        <div style={{ padding: '12px 10px', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div onClick={() => handleAvatarUpload('user')} style={{ cursor: 'pointer', position: 'relative' }} title="Change avatar">
            <AgentAvatar src={profilePicture} name={username || 'U'} size={36} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{username || 'User'}</div>
          </div>
          <button onClick={logout} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: 16, padding: 4 }} title="Logout">🚪</button>
        </div>
      </div>

      {/* ═══ Main Content ═══ */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        {!selectedAgent ? (
          /* Empty state */
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
            <EvelynEye size={64} />
            <h2 style={{ fontSize: 20, fontWeight: 700 }}>Welcome to Somniac Lab</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Select an agent or spawn a new Artificial Consciousness</p>
            <button onClick={() => setShowSpawn(true)} style={{ background: 'var(--accent)', color: 'white', border: 'none', padding: '10px 24px', borderRadius: 8, fontWeight: 600, cursor: 'pointer', marginTop: 8 }}>Spawn New AI</button>
          </div>
        ) : tab === 'chat' ? (<>
          {/* Chat header */}
          <div style={{ height: 56, borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', padding: '0 20px', gap: 12, flexShrink: 0 }}>
            <AgentAvatar src={selectedAgent.profile_picture} name={selectedAgent.name} size={32} />
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{selectedAgent.name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{aiState?.is_sleeping ? '💤 Sleeping' : 'Artificial Consciousness'}</div>
            </div>
            {aiState && <MoodBadge mood={aiState.mood} />}
          </div>
          {/* Messages */}
          <div style={{ flex: 1, overflow: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            {messages.length === 0 && !isThinking && (
              <div style={{ textAlign: 'center', marginTop: 60, color: 'var(--text-muted)' }}>
                <AgentAvatar src={selectedAgent.profile_picture} name={selectedAgent.name} size={56} />
                <p style={{ marginTop: 16, fontSize: 15 }}>{aiState?.is_sleeping ? `${selectedAgent.name} is sleeping... 💤` : `Start a conversation with ${selectedAgent.name}`}</p>
              </div>
            )}
            {messages.map(msg => <ChatMessage key={msg.id} msg={msg} agentName={selectedAgent.name} agentPic={selectedAgent.profile_picture} />)}
            {isThinking && streamBuffer && <StreamingBubble text={streamBuffer} name={selectedAgent.name} pic={selectedAgent.profile_picture} />}
            {isThinking && !streamBuffer && <TypingIndicator name={selectedAgent.name} pic={selectedAgent.profile_picture} />}
            <div ref={bottomRef} />
          </div>
          {/* Input */}
          <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
            <div style={{ position: 'relative' }}>
              <textarea ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
                placeholder={aiState?.is_sleeping ? `${selectedAgent.name} is sleeping...` : 'Type a message (Enter to send, Shift+Enter for new line)'}
                disabled={aiState?.is_sleeping || isThinking} rows={1} className="chat-input"
                style={{ maxHeight: 120, overflowY: 'auto', opacity: aiState?.is_sleeping ? 0.5 : 1 }} />
              <button onClick={handleSend} disabled={!input.trim() || isThinking || aiState?.is_sleeping}
                style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: !input.trim() || isThinking ? 'var(--border)' : 'var(--accent)', border: 'none', borderRadius: 8, padding: '6px 12px', cursor: !input.trim() || isThinking ? 'default' : 'pointer', color: 'white', fontSize: 16, fontWeight: 600, transition: 'all 0.2s' }}>
                {isThinking ? '⏳' : '↑'}
              </button>
            </div>
          </div>
        </>) : (
          /* Settings tab */
          <div style={{ padding: 40, flex: 1, overflow: 'auto' }}>
            <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Settings</h2>

            {/* Agent avatar */}
            <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 12, border: '1px solid var(--border)', marginBottom: 20 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Agent Avatar</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <AgentAvatar src={selectedAgent.profile_picture} name={selectedAgent.name} size={64} />
                <button onClick={() => handleAvatarUpload('agent', selectedAgent.id)} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 16px', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 13 }}>
                  Upload Picture
                </button>
              </div>
            </div>

            {/* WhatsApp */}
            <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 12, border: '1px solid var(--border)', marginBottom: 20 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#25D366' }}>📱</span> WhatsApp Connection
              </h3>
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', marginBottom: 8, fontSize: 13, fontWeight: 600 }}>Master Phone Number</label>
                <input type="text" value={masterPhone} onChange={e => setMasterPhone(e.target.value)} placeholder="e.g. 628123456789"
                  style={{ width: '100%', maxWidth: 300, padding: '10px 14px', borderRadius: 8, background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }} />
              </div>
              <button onClick={() => generateQr(masterPhone)} style={{ background: 'var(--accent)', color: 'white', border: 'none', padding: '10px 20px', borderRadius: 8, fontWeight: 600, cursor: 'pointer' }}>
                Generate QR
              </button>
              {qrString && (
                <div style={{ marginTop: 20, padding: 16, background: 'var(--bg-secondary)', borderRadius: 12, border: '1px solid var(--border)', display: 'inline-block' }}>
                  {qrString === 'LOADING' ? <div style={{ padding: 20, color: 'var(--text-muted)' }}>Loading...</div>
                   : qrString === 'CONNECTED' ? <div style={{ padding: 20, color: 'var(--green)', fontWeight: 600 }}>🟢 Connected!</div>
                   : <div style={{ textAlign: 'center' }}>
                       <p style={{ marginBottom: 12, fontSize: 13, color: 'var(--text-secondary)' }}>Scan with WhatsApp</p>
                       <div style={{ background: 'white', padding: 12, borderRadius: 8, display: 'inline-block' }}><QRCodeSVG value={qrString} size={180} /></div>
                     </div>}
                </div>
              )}
            </div>

            {/* Danger zone */}
            <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 12, border: '1px solid rgba(239,68,68,0.3)' }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: '#f87171' }}>Danger Zone</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>Permanently delete this agent and all its data.</p>
              <button onClick={() => setDeleteTarget(selectedAgent)} style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '8px 16px', cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>
                Delete Agent
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ═══ Right Panel ═══ */}
      {selectedAgent && (
        <div style={{ width: 280, background: 'var(--bg-panel)', borderLeft: '1px solid var(--border)', display: 'flex', flexDirection: 'column', flexShrink: 0, overflow: 'hidden' }}>
          <div style={{ padding: '16px 16px 12px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', fontWeight: 700 }}>AC Dashboard</div>
          </div>
          <StatePanel aiState={aiState} houseState={houseState} economy={economy} agentName={selectedAgent.name} agentPic={selectedAgent.profile_picture} sendCommand={sendCommand} />
        </div>
      )}

      {/* ═══ Spawn Modal ═══ */}
      {showSpawn && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: 'var(--bg-primary)', padding: 32, borderRadius: 16, width: 400, border: '1px solid var(--border)' }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>Spawn New AI</h2>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Name</label>
              <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="Evelyn" style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }} />
            </div>
            <div style={{ marginBottom: 32 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Base Persona</label>
              <textarea value={newPersona} onChange={e => setNewPersona(e.target.value)} rows={3} style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', resize: 'none' }} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => setShowSpawn(false)} disabled={creating} style={{ flex: 1, padding: 10, background: 'transparent', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-secondary)', cursor: 'pointer' }}>Cancel</button>
              <button onClick={handleCreate} disabled={creating} style={{ flex: 1, padding: 10, background: 'var(--accent)', border: 'none', borderRadius: 8, color: 'white', fontWeight: 600, cursor: 'pointer' }}>{creating ? 'Spawning...' : 'Spawn AI'}</button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ Delete Modal ═══ */}
      {deleteTarget && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: 'var(--bg-primary)', padding: 32, borderRadius: 16, width: 380, border: '1px solid rgba(239,68,68,0.3)' }}>
            <div style={{ fontSize: 36, marginBottom: 16, textAlign: 'center' }}>⚠️</div>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8, textAlign: 'center' }}>Delete Agent?</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, textAlign: 'center', marginBottom: 8 }}>Permanently delete</p>
            <p style={{ fontWeight: 700, fontSize: 16, textAlign: 'center', marginBottom: 8 }}>"{deleteTarget.name}"</p>
            <p style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', marginBottom: 28 }}>All memory, journals, and data will be erased. This cannot be undone.</p>
            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => setDeleteTarget(null)} disabled={deleting} style={{ flex: 1, padding: 10, background: 'transparent', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-secondary)', cursor: 'pointer' }}>Cancel</button>
              <button onClick={handleDelete} disabled={deleting} style={{ flex: 1, padding: 10, background: '#ef4444', border: 'none', borderRadius: 8, color: 'white', fontWeight: 700, cursor: 'pointer', opacity: deleting ? 0.6 : 1 }}>{deleting ? 'Deleting...' : 'Yes, Delete'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
