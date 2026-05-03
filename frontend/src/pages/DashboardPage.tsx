import { useState, useRef, useEffect, KeyboardEvent, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { MessageSquare, Book, Settings, LogOut, Send, AlertTriangle, Smartphone, Plus } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useAIConnection, type Message } from '../hooks/useAIConnection'
import { AgentAvatar, EvelynEye } from '../components/ui/LabComponents'
import StatePanel from '../components/ui/StatePanel'

import { motion, AnimatePresence } from 'framer-motion'
import { ShoppingBag, Newspaper, Hash } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Agent { id: number; name: string; persona: string; mood: string; profile_picture?: string | null; banner_picture?: string | null; model_provider?: string; discord_connected?: boolean }

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
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="chat-message-inline telegram-anim" style={{ display: 'flex', gap: 16, marginTop: 4 }}>
      <div style={{ marginTop: 2, cursor: isUser ? 'default' : 'pointer' }} onClick={() => { if(!isUser && (window as any).openAiProfile) (window as any).openAiProfile() }}>
        {isUser ? (
          <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--bg-panel)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>You</div>
        ) : (
          <AgentAvatar src={agentPic} name={agentName} size={40} />
        )}
      </div>
      <div style={{ flex: 1, position: 'relative' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
          <span style={{ fontWeight: 600, fontSize: 15, color: isUser ? 'var(--text-primary)' : 'var(--accent)' }}>
            {isUser ? 'You' : agentName}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{formatTime(msg.ts)}</span>
        </div>
        <p style={{ fontSize: 15, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{msg.text}</p>
        
        {/* Simple floating emoji logic if message contains emoji */}
        {!isUser && msg.text && [...msg.text].find(c => c.length > 1 || c.match(/\p{Emoji}/u)) && (
           <motion.div initial={{ scale: 0, opacity: 0, y: 0 }} animate={{ scale: [0, 1.5, 1], opacity: [0, 1, 0], y: -50 }} transition={{ duration: 1.5, ease: "easeOut" }} style={{ position: 'absolute', top: 0, right: 20, fontSize: 32, pointerEvents: 'none' }}>
             {[...msg.text].find(c => c.length > 1 || c.match(/\p{Emoji}/u))}
           </motion.div>
        )}
      </div>
    </motion.div>
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
  const [tab, setTab] = useState<'chat' | 'settings' | 'shop' | 'news'>('chat')
  const [input, setInput] = useState('')
  const [masterPhone, setMasterPhone] = useState('')
  const [showSpawn, setShowSpawn] = useState(false)
  const [newName, setNewName] = useState('Evelyn')
  const [newPersona, setNewPersona] = useState('Helpful and friendly AI assistant.')
  const [newProfilePic, setNewProfilePic] = useState<string | null>(null)
  const [newBannerPic, setNewBannerPic] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Agent | null>(null)
  const [deleting, setDeleting] = useState(false)
  
  // Profile modal
  const [showProfile, setShowProfile] = useState(false)
  // Shop & Inventory
  const [shopItems, setShopItems] = useState<any[]>([])
  const [inventory, setInventory] = useState<any[]>([])
  const [newsPosts, setNewsPosts] = useState<any[]>([])
  const [timezone, setTimezone] = useState('Asia/Jakarta')
  const [savingSettings, setSavingSettings] = useState(false)
  
  const [discordToken, setDiscordToken] = useState('')
  const [discordChannelId, setDiscordChannelId] = useState('')
  const [discordConnecting, setDiscordConnecting] = useState(false)

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

  const fetchProfileAndShop = useCallback(async () => {
    try {
      const pRes = await fetch(`${API_URL}/api/profile`, { headers: { Authorization: `Bearer ${token}` } })
      if (pRes.ok) {
        const p = await pRes.json()
        setInventory(p.inventory || [])
        setTimezone(p.timezone || 'Asia/Jakarta')
      }
      const sRes = await fetch(`${API_URL}/api/shop`, { headers: { Authorization: `Bearer ${token}` } })
      if (sRes.ok) setShopItems(await sRes.json())
    } catch {}
  }, [token])

  useEffect(() => { fetchAgents(); fetchProfileAndShop() }, [fetchAgents, fetchProfileAndShop])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, isThinking, streamBuffer])
  useEffect(() => { (window as any).openAiProfile = () => setShowProfile(true) }, [])

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
      const res = await fetch(`${API_URL}/api/agents`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ name: newName, base_persona: newPersona, profile_picture: newProfilePic, banner_picture: newBannerPic }) })
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

  const handleSaveSettings = async () => {
    setSavingSettings(true)
    try {
      await fetch(`${API_URL}/api/user/settings`, { method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ timezone }) })
    } catch {} finally { setSavingSettings(false) }
  }

  const handleDiscordConnect = async () => {
    if (!selectedAgent) return
    setDiscordConnecting(true)
    try {
        const res = await fetch(`${API_URL}/api/agents/${selectedAgent.id}/discord/sync`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({ token: discordToken, channel_id: discordChannelId })
        })
        if (res.ok) {
            await fetchAgents()
            setDiscordToken('')
            setDiscordChannelId('')
        }
    } catch (e) {
        console.error(e)
    } finally {
        setDiscordConnecting(false)
    }
  }

  const handleDiscordDisconnect = async () => {
    if (!selectedAgent) return
    setDiscordConnecting(true)
    try {
        const res = await fetch(`${API_URL}/api/agents/${selectedAgent.id}/discord/disconnect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
            await fetchAgents()
        }
    } catch (e) {
        console.error(e)
    } finally {
        setDiscordConnecting(false)
    }
  }

  const buyItem = async (item: any) => {
    try {
      const res = await fetch(`${API_URL}/api/shop/buy`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ item_id: item.id, name: item.name, emoji: item.emoji, type: item.type }) })
      if (res.ok) { const d = await res.json(); setInventory(d.inventory) }
    } catch {}
  }

  const interactItem = async (action: 'feed' | 'give', item: any) => {
    if (!selectedAgent) return
    try {
      const res = await fetch(`${API_URL}/api/agents/${selectedAgent.id}/${action}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ item_id: item.id, name: item.name, emoji: item.emoji }) })
      if (res.ok) { const d = await res.json(); setInventory(d.inventory) }
    } catch {}
  }

  useEffect(() => {
    if (tab === 'news' && !selectedAgent) {
      fetch(`${API_URL}/api/news`)
        .then(res => res.json())
        .then(data => setNewsPosts(data))
        .catch(err => console.error(err))
    }
  }, [tab, selectedAgent])

  const handleAvatarUpload = async (type: 'user' | 'agent' | 'banner', agentIdNum?: number) => {
    const input = document.createElement('input')
    input.type = 'file'; input.accept = 'image/*'
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0]
      if (!file) return
      const canvas = document.createElement('canvas')
      const img = new Image()
      img.onload = async () => {
        const isBanner = type === 'banner'
        canvas.width = isBanner ? 600 : 200; canvas.height = isBanner ? 200 : 200
        const ctx = canvas.getContext('2d')!
        
        if (isBanner) {
          const ratio = Math.max(600 / img.width, 200 / img.height)
          const newW = img.width * ratio, newH = img.height * ratio
          ctx.drawImage(img, (600 - newW) / 2, (200 - newH) / 2, newW, newH)
        } else {
          const s = Math.min(img.width, img.height)
          ctx.drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, 0, 0, 200, 200)
        }
        
        const dataUrl = canvas.toDataURL('image/webp', 0.8)
        
        if (type === 'user') {
          await fetch(`${API_URL}/api/profile/picture`, { method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ image: dataUrl }) })
          setProfilePicture(dataUrl)
        } else if (agentIdNum) {
          const url = isBanner ? `${API_URL}/api/agents/${agentIdNum}/banner` : `${API_URL}/api/agents/${agentIdNum}/picture`
          await fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ image: dataUrl }) })
          await fetchAgents()
        } else {
          // Pre-creation upload
          if (isBanner) setNewBannerPic(dataUrl)
          else setNewProfilePic(dataUrl)
        }
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
        <div onClick={() => { navigate('/lab'); setTab('chat') }} className="btn-press avatar-rail-container" style={{ cursor: 'pointer', marginBottom: 8 }}>
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
            <div className={`sidebar-item btn-press ${tab === 'shop' ? 'active' : ''}`} onClick={() => setTab('shop')}>
              <ShoppingBag size={18} /> Shop & Inventory
            </div>
            <div className="sidebar-item" style={{ opacity: 0.4, cursor: 'not-allowed' }}>
              <Book size={18} /> Journal
            </div>
            <div className={`sidebar-item btn-press ${tab === 'settings' ? 'active' : ''}`} onClick={() => setTab('settings')}>
              <Settings size={18} /> Settings
            </div>
          </div>
        </>) : (<>
          <div style={{ padding: '24px 16px', color: 'var(--text-muted)', fontSize: 14 }}>
            <p style={{ marginBottom: 8, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>Somniac Lab</p>
            <p style={{ lineHeight: 1.5 }}>Select an AI agent from the left rail, or create a new one to begin.</p>
          </div>
          <div style={{ padding: '16px 12px', flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div className={`sidebar-item btn-press ${tab === 'news' ? 'active' : ''}`} onClick={() => setTab('news')}>
              <Newspaper size={18} /> Somniac News
            </div>
          </div>
        </>)}

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
          tab === 'news' ? (
            <div className="telegram-anim" style={{ padding: 40, flex: 1, overflow: 'auto' }}>
              <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32, letterSpacing: '-0.5px', display: 'flex', alignItems: 'center', gap: 12 }}>
                <Newspaper size={28} style={{ color: 'var(--accent)' }}/> Somniac News
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 800 }}>
                {newsPosts.map((post) => (
                  <motion.div key={post.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} 
                    style={{ background: 'var(--bg-card)', borderRadius: 16, border: '1px solid var(--border)', overflow: 'hidden', boxShadow: '0 4px 20px rgba(0,0,0,0.1)', transition: 'transform 0.2s', cursor: 'default' }}
                    whileHover={{ scale: 1.01 }}>
                    {post.banner_image && (
                      <div style={{ width: '100%', height: 200, background: 'var(--bg-panel)' }}>
                        <img src={post.banner_image} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      </div>
                    )}
                    <div style={{ padding: 24 }}>
                      <div style={{ fontSize: 12, color: 'var(--accent)', fontWeight: 700, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>{new Date(post.created_at * 1000).toLocaleDateString()} • {post.author}</div>
                      <h3 style={{ fontSize: 24, fontWeight: 800, marginBottom: 16 }}>{post.title}</h3>
                      <div className="news-content" style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: 15 }} dangerouslySetInnerHTML={{ __html: post.content }} />
                    </div>
                  </motion.div>
                ))}
                {newsPosts.length === 0 && <div style={{ color: 'var(--text-muted)' }}>No news currently available.</div>}
              </div>
            </div>
          ) : (
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
          )
        ) : tab === 'chat' ? (<>
          {/* Chat header */}
          <div style={{ height: 64, borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', padding: '0 24px', gap: 16, flexShrink: 0, background: 'var(--bg-primary)', boxShadow: '0 1px 2px rgba(0,0,0,0.1)', zIndex: 10 }}>
            <div onClick={() => setShowProfile(true)} style={{ cursor: 'pointer' }} className="btn-press">
              <AgentAvatar src={selectedAgent.profile_picture} name={selectedAgent.name} size={40} />
            </div>
            <div style={{ flex: 1, cursor: 'pointer' }} onClick={() => setShowProfile(true)}>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{selectedAgent.name}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{aiState?.is_sleeping ? '💤 System asleep' : houseState?.chore_step_label || 'Consciousness active'}</div>
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
        </> ) : tab === 'shop' ? (
          <div className="telegram-anim" style={{ padding: 40, flex: 1, overflow: 'auto' }}>
            <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32, letterSpacing: '-0.5px', display: 'flex', alignItems: 'center', gap: 12 }}>
              <ShoppingBag size={28} style={{ color: 'var(--accent)' }}/> Shop & Inventory
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32 }}>
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, color: 'var(--text-secondary)' }}>Market</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {shopItems.map(item => (
                    <div key={item.id} style={{ background: 'var(--bg-card)', padding: 16, borderRadius: 12, border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 16 }}>
                      <div style={{ fontSize: 32 }}>{item.emoji}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 700 }}>{item.name}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.description}</div>
                      </div>
                      <button onClick={() => buyItem(item)} className="btn-press" style={{ background: 'var(--bg-panel)', color: 'var(--text-primary)', border: '1px solid var(--border)', padding: '6px 12px', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>Buy (Free)</button>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, color: 'var(--text-secondary)' }}>My Inventory</h3>
                {inventory.length === 0 ? (
                  <div style={{ padding: 32, textAlign: 'center', background: 'var(--bg-panel)', borderRadius: 12, color: 'var(--text-muted)', fontSize: 14 }}>Your inventory is empty.</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {inventory.map(item => (
                      <div key={item.id} style={{ background: 'var(--bg-card)', padding: 16, borderRadius: 12, border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 16 }}>
                        <div style={{ fontSize: 32 }}>{item.emoji}</div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 700 }}>{item.name}</div>
                          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Owned: {item.qty}</div>
                        </div>
                        <div style={{ display: 'flex', gap: 8 }}>
                          {item.type === 'food' && (
                            <button onClick={() => interactItem('feed', item)} className="btn-press" style={{ background: 'var(--accent)', color: 'var(--bg-primary)', border: 'none', padding: '6px 12px', borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>Feed AI</button>
                          )}
                          <button onClick={() => interactItem('give', item)} className="btn-press" style={{ background: 'var(--bg-panel)', color: 'var(--text-primary)', border: '1px solid var(--border)', padding: '6px 12px', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>Give</button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Settings tab */
          <div className="telegram-anim" style={{ padding: 40, flex: 1, overflow: 'auto' }}>
            <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32, letterSpacing: '-0.5px' }}>Settings</h2>

            {/* User Settings */}
            <div style={{ background: 'var(--bg-card)', padding: 32, borderRadius: 16, border: '1px solid var(--border)', marginBottom: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20 }}>User Preferences</h3>
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', marginBottom: 8, fontSize: 13, fontWeight: 600, color: 'var(--text-muted)' }}>Timezone</label>
                <div style={{ display: 'flex', gap: 12 }}>
                  <input type="text" value={timezone} onChange={e => setTimezone(e.target.value)} placeholder="e.g. Asia/Jakarta"
                    style={{ flex: 1, maxWidth: 360, padding: '12px 16px', borderRadius: 8, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 14, outline: 'none' }} />
                  <button onClick={handleSaveSettings} disabled={savingSettings} className="btn-press" style={{ background: 'var(--text-primary)', color: 'var(--bg-primary)', border: 'none', padding: '10px 24px', borderRadius: 8, fontWeight: 600, cursor: 'pointer' }}>
                    {savingSettings ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </div>
            </div>

            {/* Agent avatar & banner */}
            <div style={{ background: 'var(--bg-card)', padding: 32, borderRadius: 16, border: '1px solid var(--border)', marginBottom: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20 }}>Agent Profile Customization</h3>
              
              <div style={{ marginBottom: 24 }}>
                <label style={{ display: 'block', marginBottom: 8, fontSize: 13, fontWeight: 600, color: 'var(--text-muted)' }}>Banner Image</label>
                <div style={{ position: 'relative', width: '100%', height: 120, background: 'var(--bg-panel)', borderRadius: 12, overflow: 'hidden', border: '1px solid var(--border)', marginBottom: 12 }}>
                  {selectedAgent.banner_picture ? <img src={selectedAgent.banner_picture} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No Banner</div>}
                </div>
                <button onClick={() => handleAvatarUpload('banner', selectedAgent.id)} className="btn-press" style={{ background: 'var(--bg-panel)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 16px', cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>Change Banner</button>
              </div>

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

            {/* Discord */}
            <div style={{ background: 'var(--bg-card)', padding: 32, borderRadius: 16, border: '1px solid var(--border)', marginBottom: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
                <Hash size={20} style={{ color: '#5865F2' }} /> Discord Autonomy Sync
              </h3>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 20, lineHeight: 1.6 }}>
                Give this agent a Discord bot token to allow them to autonomously read a timeline channel and post / DM you. Token is encrypted in the database.
              </p>
              
              {selectedAgent.discord_connected ? (
                <div className="telegram-anim" style={{ marginTop: 24, padding: 24, background: 'var(--bg-primary)', borderRadius: 16, border: '1px solid var(--border)', display: 'inline-block' }}>
                   <div style={{ padding: 10, color: 'var(--green)', fontWeight: 600, marginBottom: 12 }}>🟢 Discord Connected Successfully!</div>
                   <button onClick={handleDiscordDisconnect} disabled={discordConnecting} className="btn-press" style={{ background: 'var(--bg-panel)', color: 'var(--text-primary)', border: '1px solid var(--border)', padding: '10px 24px', borderRadius: 8, fontWeight: 600, cursor: 'pointer' }}>
                     {discordConnecting ? 'Disconnecting...' : 'Disconnect Bot'}
                   </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 360 }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: 8, fontSize: 13, fontWeight: 600, color: 'var(--text-muted)' }}>BOT TOKEN</label>
                    <input type="password" value={discordToken} onChange={e => setDiscordToken(e.target.value)} placeholder="Paste bot token here..."
                      style={{ width: '100%', padding: '12px 16px', borderRadius: 8, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 14, outline: 'none' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', marginBottom: 8, fontSize: 13, fontWeight: 600, color: 'var(--text-muted)' }}>TIMELINE CHANNEL ID</label>
                    <input type="text" value={discordChannelId} onChange={e => setDiscordChannelId(e.target.value)} placeholder="e.g. 1234567890"
                      style={{ width: '100%', padding: '12px 16px', borderRadius: 8, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 14, outline: 'none' }} />
                  </div>
                  <button onClick={handleDiscordConnect} disabled={discordConnecting || !discordToken || !discordChannelId} className="btn-press" style={{ background: 'var(--text-primary)', color: 'var(--bg-primary)', border: 'none', padding: '12px 24px', borderRadius: 8, fontWeight: 600, cursor: (discordConnecting || !discordToken || !discordChannelId) ? 'default' : 'pointer', opacity: (discordConnecting || !discordToken || !discordChannelId) ? 0.5 : 1 }}>
                    {discordConnecting ? 'Connecting...' : 'Connect Discord'}
                  </button>
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
            <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 8, color: 'var(--text-muted)' }}>AVATAR (Optional)</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <AgentAvatar src={newProfilePic} name={newName} size={48} />
                  <button onClick={() => handleAvatarUpload('agent')} className="btn-press" style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '6px 12px', borderRadius: 8, fontSize: 12, cursor: 'pointer' }}>Upload</button>
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 8, color: 'var(--text-muted)' }}>BANNER (Optional)</label>
                <button onClick={() => handleAvatarUpload('banner')} className="btn-press" style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '6px 12px', borderRadius: 8, fontSize: 12, cursor: 'pointer' }}>
                  {newBannerPic ? 'Banner Uploaded ✓' : 'Upload Banner'}
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => {setShowSpawn(false); setNewProfilePic(null); setNewBannerPic(null)}} disabled={creating} className="btn-press" style={{ flex: 1, padding: 14, background: 'transparent', border: '1px solid var(--border)', borderRadius: 12, color: 'var(--text-primary)', cursor: 'pointer', fontWeight: 600 }}>Cancel</button>
              <button onClick={handleCreate} disabled={creating} className="btn-press" style={{ flex: 1, padding: 14, background: 'var(--text-primary)', border: 'none', borderRadius: 12, color: 'var(--bg-primary)', fontWeight: 700, cursor: 'pointer' }}>{creating ? 'Spawning...' : 'Spawn AI'}</button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ AI Profile Modal (Discord style) ═══ */}
      <AnimatePresence>
        {showProfile && selectedAgent && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }} onClick={() => setShowProfile(false)}>
            <motion.div initial={{ scale: 0.95, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0, y: 20 }} onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-card)', width: 340, borderRadius: 16, overflow: 'hidden', boxShadow: '0 24px 48px rgba(0,0,0,0.5)', border: '1px solid var(--border)' }}>
              {/* Banner */}
              <div style={{ width: '100%', height: 120, background: selectedAgent.banner_picture ? `url(${selectedAgent.banner_picture}) center/cover` : 'var(--accent)' }} />
              {/* Profile Body */}
              <div style={{ padding: '0 16px 16px', position: 'relative' }}>
                <div style={{ position: 'absolute', top: -40, left: 16, border: '6px solid var(--bg-card)', borderRadius: '50%', background: 'var(--bg-card)' }}>
                  <AgentAvatar src={selectedAgent.profile_picture} name={selectedAgent.name} size={80} />
                  <div style={{ position: 'absolute', bottom: 4, right: 4, width: 16, height: 16, borderRadius: '50%', background: aiState?.is_sleeping ? 'var(--text-muted)' : 'var(--green)', border: '3px solid var(--bg-card)' }} />
                </div>
                
                <div style={{ marginTop: 50, background: 'var(--bg-panel)', padding: 16, borderRadius: 12 }}>
                  <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>{selectedAgent.name}</h3>
                  <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>Somniac AI Entity</div>
                  
                  <div style={{ width: '100%', height: 1, background: 'var(--border)', margin: '12px 0' }} />
                  
                  <h4 style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>Current Activity</h4>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>
                    <span>{aiState?.is_sleeping ? '💤' : houseState?.current_chore_emoji || '🛋️'}</span>
                    <span>{aiState?.is_sleeping ? 'Sleeping' : houseState?.chore_step_label || 'Chilling at home'}</span>
                  </div>
                  
                  <div style={{ width: '100%', height: 1, background: 'var(--border)', margin: '12px 0' }} />
                  
                  <h4 style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>Bio</h4>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {selectedAgent.persona}
                  </p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

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
