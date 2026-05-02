import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface Agent {
  id: number
  name: string
  persona: string
  mood: string
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function DashboardPage() {
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  // Modal state
  const [showModal, setShowModal] = useState(false)
  const [newName, setNewName] = useState('Evelyn')
  const [newPersona, setNewPersona] = useState('Helpful and friendly AI assistant.')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    try {
      const res = await fetch(`${API_URL}/api/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setAgents(data)
      }
    } catch (err) {
      console.error('Failed to fetch agents', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!newName.trim() || !newPersona.trim()) return
    setCreating(true)
    try {
      const res = await fetch(`${API_URL}/api/agents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ name: newName, base_persona: newPersona })
      })
      if (res.ok) {
        const agent = await res.json()
        setAgents([...agents, { id: agent.id, name: agent.name, persona: agent.persona, mood: 'netral' }])
        setShowModal(false)
        navigate(`/lab/${agent.id}`)
      }
    } catch (err) {
      console.error('Failed to create agent', err)
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}>
        <div style={{ animation: 'spin 1s linear infinite', width: 30, height: 30, border: '3px solid var(--border)', borderTopColor: 'var(--accent)', borderRadius: '50%' }} />
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', display: 'flex', flexDirection: 'column' }}>
      
      {/* Navbar */}
      <header style={{ height: 64, borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', padding: '0 32px', justifyContent: 'space-between' }}>
        <Link to="/" style={{ fontWeight: 700, fontSize: 18, color: 'var(--text-primary)', textDecoration: 'none' }}>somniac</Link>
        <button onClick={logout} style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-secondary)', padding: '6px 12px', borderRadius: 8, cursor: 'pointer' }}>
          Logout
        </button>
      </header>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '48px 32px', maxWidth: 1000, margin: '0 auto', width: '100%' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 40 }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Your AI Agents</h1>
            <p style={{ color: 'var(--text-secondary)' }}>Select an instance to connect or create a new Artificial Consciousness.</p>
          </div>
          <button 
            onClick={() => setShowModal(true)}
            style={{
              background: 'var(--text-primary)',
              color: 'var(--bg-primary)',
              border: 'none',
              padding: '10px 20px',
              borderRadius: 8,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              transition: 'background 0.2s'
            }}
          >
            <span>+</span> Spawn New AI
          </button>
        </div>

        {agents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 16 }}>
            <div style={{ fontSize: 40, marginBottom: 16 }}>🤖</div>
            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>No agents found</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>You haven't spawned any AI instances yet.</p>
            <button onClick={() => setShowModal(true)} style={{ background: 'var(--accent)', color: 'white', padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontWeight: 600 }}>
              Create First Agent
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 24 }}>
            {agents.map(agent => (
              <div 
                key={agent.id}
                onClick={() => navigate(`/lab/${agent.id}`)}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: 16,
                  padding: 24,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  position: 'relative',
                  overflow: 'hidden'
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--text-primary)'
                  e.currentTarget.style.transform = 'translateY(-2px)'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border)'
                  e.currentTarget.style.transform = 'translateY(0)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                  <div style={{ fontWeight: 700, fontSize: 18, display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--green)', boxShadow: '0 0 8px var(--green)' }} />
                    {agent.name}
                  </div>
                  <span className="badge" style={{ fontSize: 11, background: 'rgba(52,211,153,0.1)', color: '#34d399' }}>
                    {agent.mood || 'Netral'}
                  </span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {agent.persona}
                </p>
                <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--text-muted)' }}>
                  ID: {agent.id} • Offline
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Spawn Modal */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: 'var(--bg-primary)', padding: 32, borderRadius: 16, width: 400, border: '1px solid var(--border)' }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>Spawn New AI</h2>
            
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Name</label>
              <input 
                value={newName} 
                onChange={e => setNewName(e.target.value)} 
                placeholder="Evelyn"
                style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              />
            </div>
            
            <div style={{ marginBottom: 32 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Base Persona</label>
              <textarea 
                value={newPersona} 
                onChange={e => setNewPersona(e.target.value)} 
                rows={3}
                placeholder="Helpful and friendly AI assistant."
                style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', resize: 'none' }}
              />
            </div>
            
            <div style={{ display: 'flex', gap: 12 }}>
              <button 
                onClick={() => setShowModal(false)}
                disabled={creating}
                style={{ flex: 1, padding: 10, background: 'transparent', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-secondary)', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button 
                onClick={handleCreate}
                disabled={creating}
                style={{ flex: 1, padding: 10, background: 'var(--text-primary)', border: 'none', borderRadius: 8, color: 'var(--bg-primary)', fontWeight: 600, cursor: 'pointer' }}
              >
                {creating ? 'Spawning...' : 'Spawn AI'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
