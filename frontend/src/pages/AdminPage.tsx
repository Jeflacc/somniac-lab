import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { Trash2, Upload, PlusCircle, ArrowLeft } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function AdminPage() {
  const { username, token } = useAuth()
  const navigate = useNavigate()

  const [posts, setPosts] = useState<any[]>([])
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [bannerBase64, setBannerBase64] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (username !== 'jeflacc') {
      // Access Denied handling - just wait a moment to see if user loads
      if (username) {
         navigate('/lab')
      }
      return
    }
    
    fetchNews()
  }, [username, navigate])

  const fetchNews = async () => {
    setIsLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/news`)
      const data = await res.json()
      setPosts(data)
    } catch (e) {
      console.error('Failed to fetch news', e)
    } finally {
      setIsLoading(false)
    }
  }

  const handleBannerUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      if (ev.target?.result) {
        setBannerBase64(ev.target.result as string)
      }
    }
    reader.readAsDataURL(file)
  }

  const handleSubmit = async () => {
    if (!title || !content) return alert('Title and content are required')
    setIsSubmitting(true)
    try {
      const res = await fetch(`${API_URL}/api/news`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title,
          content,
          banner_image: bannerBase64
        })
      })
      if (!res.ok) throw new Error('Failed to post')
      
      setTitle('')
      setContent('')
      setBannerBase64(null)
      fetchNews()
      alert('News published successfully!')
    } catch (e) {
      alert(String(e))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this post?')) return
    try {
      const res = await fetch(`${API_URL}/api/news/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!res.ok) throw new Error('Failed to delete')
      fetchNews()
    } catch (e) {
      alert(String(e))
    }
  }

  // Modules for ReactQuill
  const modules = {
    toolbar: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike', 'blockquote'],
      [{'list': 'ordered'}, {'list': 'bullet'}, {'indent': '-1'}, {'indent': '+1'}],
      ['link', 'image'],
      [{ 'color': [] }, { 'background': [] }],
      ['clean']
    ],
  }

  if (username !== 'jeflacc') {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000', color: '#0f0', fontFamily: 'monospace' }}>
        <h2>ACCESS DENIED. USER IDENTIFICATION: {username || 'UNKNOWN'}</h2>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', padding: 40, color: 'var(--text-primary)' }}>
      <div style={{ maxWidth: 1000, margin: '0 auto' }}>
        
        <button onClick={() => navigate('/lab')} className="btn-press" style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', marginBottom: 24, fontWeight: 600 }}>
          <ArrowLeft size={18} /> Back to Lab
        </button>

        <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 8, letterSpacing: '-1px' }}>Somniac Admin Portal</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 40 }}>Welcome, Master Jeflacc. Manage the Somniac News network here.</p>
        
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 32 }}>
          {/* Editor Side */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ background: 'var(--bg-card)', padding: 32, borderRadius: 16, border: '1px solid var(--border)', boxShadow: '0 12px 32px rgba(0,0,0,0.2)' }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
              <PlusCircle size={20} style={{ color: 'var(--accent)' }}/> Create New Post
            </h2>
            
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 700, marginBottom: 8, color: 'var(--text-muted)' }}>POST TITLE</label>
              <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Somniac v2.0 is Here!" style={{ width: '100%', padding: '12px 16px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-primary)', color: 'var(--text-primary)', outline: 'none', fontSize: 18, fontWeight: 600 }} />
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 700, marginBottom: 8, color: 'var(--text-muted)' }}>BANNER IMAGE (Base64)</label>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                <div style={{ width: 160, height: 90, background: 'var(--bg-panel)', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)' }}>
                  {bannerBase64 ? <img src={bannerBase64} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12 }}>No Banner</div>}
                </div>
                <div style={{ flex: 1 }}>
                  <input type="file" id="banner-upload" accept="image/*" onChange={handleBannerUpload} style={{ display: 'none' }} />
                  <button onClick={() => document.getElementById('banner-upload')?.click()} className="btn-press" style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '10px 16px', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Upload size={16} /> Upload Banner
                  </button>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 700, marginBottom: 8, color: 'var(--text-muted)' }}>CONTENT EDITOR</label>
              <div style={{ background: 'white', borderRadius: 8, overflow: 'hidden', color: 'black' }}>
                {/* ReactQuill requires a wrapper for light mode styles typically, we enforce white bg so quill looks normal */}
                <ReactQuill theme="snow" value={content} onChange={setContent} modules={modules} style={{ height: 300, background: '#fff' }} />
              </div>
            </div>

            <div style={{ marginTop: 60, display: 'flex', justifyContent: 'flex-end' }}>
               <button onClick={handleSubmit} disabled={isSubmitting || !title || !content} className="btn-press" style={{ background: 'var(--text-primary)', color: 'var(--bg-primary)', border: 'none', padding: '12px 32px', borderRadius: 8, fontWeight: 700, cursor: isSubmitting || !title || !content ? 'not-allowed' : 'pointer', opacity: isSubmitting || !title || !content ? 0.5 : 1 }}>
                 {isSubmitting ? 'Publishing...' : 'Publish Post'}
               </button>
            </div>
          </motion.div>

          {/* Posts List Side */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Manage Posts</h2>
            {isLoading ? (
               <div style={{ color: 'var(--text-muted)' }}>Loading network...</div>
            ) : posts.length === 0 ? (
               <div style={{ padding: 24, background: 'var(--bg-panel)', borderRadius: 12, border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text-muted)' }}>No news found. Start writing!</div>
            ) : (
               posts.map(p => (
                 <div key={p.id} style={{ background: 'var(--bg-card)', padding: 16, borderRadius: 12, border: '1px solid var(--border)' }}>
                   <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                     <div>
                       <h3 style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{p.title}</h3>
                       <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{new Date(p.created_at * 1000).toLocaleString()}</div>
                     </div>
                     <button onClick={() => handleDelete(p.id)} className="btn-press" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: 'none', padding: 8, borderRadius: 8, cursor: 'pointer' }} title="Delete">
                       <Trash2 size={16} />
                     </button>
                   </div>
                 </div>
               ))
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
