import { StatBar, barColor, MoodBadge, SectionTitle, QuickBtn, AgentAvatar } from './LabComponents'
import { Moon, Sun, Utensils } from 'lucide-react'
import type { AIState } from '../../hooks/useAIConnection'

export default function StatePanel({ aiState, houseState, economy, agentName, agentPic, agentBanner, agentDecoration, sendCommand }: {
  aiState: AIState | null
  houseState: any
  economy: any
  agentName: string
  agentPic?: string | null
  agentBanner?: string | null
  agentDecoration?: string | null
  sendCommand: (cmd: string, payload?: string) => void
}) {
  if (!aiState) {
    return (
      <div style={{ padding: 20, color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', paddingTop: 40 }}>
        <div style={{ animation: 'spin 1s linear infinite', width: 20, height: 20, border: '2px solid var(--border)', borderTopColor: 'var(--accent)', borderRadius: '50%', margin: '0 auto 12px' }} />
        Connecting...
      </div>
    )
  }

  const choreIcons: Record<string, string> = {
    eat: '🍳', mandi: '🚿', sleep_routine: '😴', wake_routine: '🥱',
    play_console: '🎮', watch_tv: '📺', wander: '🚶', laundry: '👕',
    online_shopping: '🛒', check_wa: '📱',
  }

  return (
    <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 20, overflow: 'auto', flex: 1 }}>
      {/* Agent header */}
      {/* Agent header with banner background */}
      <div style={{ position: 'relative', overflow: 'hidden', borderRadius: 12, border: '1px solid var(--border)', marginBottom: 4, flexShrink: 0 }}>
        {/* Banner Background */}
        <div style={{ 
          position: 'absolute', inset: 0, 
          background: agentBanner ? `url(${agentBanner}) center/cover` : 'linear-gradient(135deg, #5865f2, #eb459e)',
          opacity: 0.85,
          zIndex: 0 
        }} />
        {/* Gradient overlay for text readability */}
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to right, var(--bg-card) 20%, transparent)', zIndex: 0 }} />
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', position: 'relative', zIndex: 1 }}>
          <AgentAvatar src={agentPic} name={agentName} decoration={agentDecoration} size={48} />
          <div>
            <div style={{ fontWeight: 800, fontSize: 16, textShadow: '0 2px 4px rgba(0,0,0,0.4)', color: 'white', marginBottom: 4 }}>{agentName}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
               <MoodBadge mood={aiState.mood} />
               <span style={{ color: '#f87171', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4, background: 'rgba(0,0,0,0.4)', padding: '2px 8px', borderRadius: 12, backdropFilter: 'blur(4px)', fontWeight: 700 }}>
                 <span style={{ animation: 'pulse-glow 1s infinite' }}>♥</span> {aiState.heart_rate} bpm
               </span>
            </div>
          </div>
        </div>
      </div>

      {/* Biology */}
      <div>
        <SectionTitle>Biology</SectionTitle>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 10 }}>
          <StatBar label="Hunger" value={aiState.hunger} color={barColor(aiState.hunger)} />
          <StatBar label="Sleepiness" value={aiState.sleepiness} color={barColor(aiState.sleepiness)} />
          <StatBar label="Libido" value={aiState.libido} color="var(--accent-2)" />
        </div>
      </div>

      {/* Activity */}
      <div>
        <SectionTitle>Activity</SectionTitle>
        <div style={{ marginTop: 8 }}>
          {houseState?.current_chore_id ? (
            <span className="badge" style={{ background: 'var(--accent-glow)', color: 'var(--accent)', fontSize: 11 }}>
              {choreIcons[houseState.current_chore_id] || '⚙️'} {houseState.current_chore_id.replace(/_/g, ' ')}
            </span>
          ) : (
            <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Idle</span>
          )}
          {houseState?.chore_step_label && (
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{houseState.chore_step_label}</p>
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

      {/* Quick Actions */}
      <div>
        <SectionTitle>Quick Actions</SectionTitle>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 12 }}>
          <QuickBtn onClick={() => sendCommand('sleep')} icon={<Moon size={16} />} label="Put to Sleep" />
          <QuickBtn onClick={() => sendCommand('wake')} icon={<Sun size={16} />} label="Wake Up" />
          <QuickBtn onClick={() => sendCommand('feed', 'nasi goreng')} icon={<Utensils size={16} />} label="Feed" />
        </div>
      </div>
    </div>
  )
}
