import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

export type AIState = {
  hunger:      number
  sleepiness:  number
  libido:      number
  mood:        string
  is_sleeping: boolean
  heart_rate:  number
  breath_rate: number
  relationship: string
  known_users: Record<string, { display_name: string; notes: string }>
  core_memories: string[]
}

export type Message = {
  id:     string
  role:   'user' | 'ai' | 'system'
  text:   string
  ts:     number
}

export type HouseState = {
  current_chore_id: string | null
  current_chore_label: string | null
  boredom: number
  showers_today: number
  dirty_laundry_count: number
}

export type EconomyState = {
  balance: number
  formatted_balance: string
}

export function useAIConnection(agentId: string | undefined) {
  const wsRef        = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout>>()
  const { token }    = useAuth()

  const [connected,  setConnected]  = useState(false)
  const [aiState,    setAiState]    = useState<AIState | null>(null)
  const [houseState, setHouseState] = useState<HouseState | null>(null)
  const [economy,    setEconomy]    = useState<EconomyState | null>(null)
  const [messages,   setMessages]   = useState<Message[]>([])
  const [isThinking, setIsThinking] = useState(false)
  const [streamBuffer, setStreamBuffer] = useState('')
  const [qrString, setQrString] = useState<string | null>(null)
  const streamRef = useRef('')

  const addMessage = useCallback((msg: Omit<Message, 'id' | 'ts'>) => {
    setMessages(prev => [...prev, { ...msg, id: crypto.randomUUID(), ts: Date.now() }])
  }, [])

  const connect = useCallback(() => {
    if (!token || !agentId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(`${WS_URL}?token=${token}&agent_id=${agentId}`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      clearTimeout(reconnectRef.current)
    }

    ws.onclose = () => {
      setConnected(false)
      reconnectRef.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data)
        switch (data.type) {
          case 'state':
            setAiState(data.state)
            break
          case 'house_state':
            setHouseState(data)
            break
          case 'economy_state':
            setEconomy({ balance: data.balance, formatted_balance: data.formatted_balance })
            break
          case 'user_message':
            addMessage({ role: 'user', text: data.text })
            break
          case 'ai_thinking':
            setIsThinking(true)
            streamRef.current = ''
            setStreamBuffer('')
            break
          case 'ai_chunk':
            streamRef.current += data.chunk
            setStreamBuffer(streamRef.current)
            break
          case 'ai_end':
            setIsThinking(false)
            if (streamRef.current.trim()) {
              addMessage({ role: 'ai', text: streamRef.current.trim() })
            }
            streamRef.current = ''
            setStreamBuffer('')
            break
          case 'command_result':
            addMessage({ role: 'system', text: data.msg || JSON.stringify(data) })
            break
          case 'wa_qr':
            setQrString(data.qr_string)
            break
          case 'error':
            addMessage({ role: 'system', text: `⚠️ ${data.msg}` })
            break
        }
      } catch {/* ignore malformed */}
    }
  }, [addMessage])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectRef.current)
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [connect, token, agentId])

  const sendMessage = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'chat', text }))
      setIsThinking(true)
      streamRef.current = ''
      setStreamBuffer('')
    }
  }, [])

  const sendCommand = useCallback((command: string, payload?: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'command', command, payload }))
    }
  }, [])

  const generateQr = useCallback((masterPhone: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'request_qr', master_phone: masterPhone }))
      setQrString('LOADING') // indicate loading
    }
  }, [])

  return {
    connected,
    aiState,
    houseState,
    economy,
    messages,
    isThinking,
    streamBuffer,
    qrString,
    sendMessage,
    sendCommand,
    generateQr,
  }
}
