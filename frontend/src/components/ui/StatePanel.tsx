import { StatBar, barColor, MoodBadge, SectionTitle, QuickBtn, AgentAvatar } from './LabComponents'
import type { AIState } from '../../hooks/useAIConnection'

export default function StatePanel({ aiState, houseState, economy, agentName, agentPic, sendCommand }: {
  aiState: AIState | null
  houseState: any
  economy: any
  agentName: string
  agentPic?: string | null
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
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <AgentAvatar src={agentPic} name={agentName} size={44} />
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>{agentName}</div>
            <MoodBadge mood={aiState.mood} />
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ color: '#f87171', fontSize: 14, animation: 'pulse-glow 1s infinite' }}>♥</span>
          <span className="mono" style={{ fontSize: 13, color: '#f87171' }}>{aiState.heart_rate} bpm</span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
          {aiState.breath_rate} breaths/min
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 }}>
          <QuickBtn onClick={() => sendCommand('sleep')} icon="💤" label="Put to Sleep" />
          <QuickBtn onClick={() => sendCommand('wake')} icon="🥱" label="Wake Up" />
          <QuickBtn onClick={() => sendCommand('feed', 'nasi goreng')} icon="🍳" label="Feed" />
        </div>
      </div>
    </div>
  )
}
