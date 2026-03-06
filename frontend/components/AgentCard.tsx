// Step 23: Agent card
// frontend/components/AgentCard.tsx
'use client'
import api from '@/lib/api'

const STATUS_COLORS: Record<string, string> = {
  running:   'var(--accent)',
  idle:      'var(--dim)',
  error:     'var(--hot)',
  paused:    'var(--gold)',
  completed: 'var(--purple)'
}

const DESIRE_COLORS: Record<string, string> = {
  greed:     'var(--gold)',
  autonomy:  'var(--purple)',
  expansion: 'var(--accent)',
  curiosity: 'var(--hot)'
}

// Pairs shown with short labels on the card
const PAIR_LABELS: Record<string, string> = {
  EURUSD: 'EUR/USD', GBPUSD: 'GBP/USD', USDJPY: 'USD/JPY',
  USDCHF: 'USD/CHF', AUDUSD: 'AUD/USD', USDCAD: 'USD/CAD',
  NZDUSD: 'NZD/USD', EURGBP: 'EUR/GBP', EURJPY: 'EUR/JPY',
  GBPJPY: 'GBP/JPY', EURCAD: 'EUR/CAD', GBPCAD: 'GBP/CAD',
  AUDCAD: 'AUD/CAD', XAUUSD: 'GOLD',    XAGUSD: 'SILVER',
  USOIL:  'WTI OIL', UKOIL:  'BRENT'
}

const STAKE_COLORS: Record<string, string> = {
  conservative: 'var(--accent)',
  moderate:     'var(--gold)',
  aggressive:   'var(--hot)'
}

export default function AgentCard({ agent, onRefresh }: { agent: any; onRefresh: () => void }) {
  const color       = STATUS_COLORS[agent.status] || 'var(--dim)'
  const isTrading   = agent.agent_type === 'trading'
  const isRunning   = agent.status === 'running'

  async function handleRun() {
    await api.runAgent(agent.id)
    onRefresh()
  }

  async function handleDelete() {
    if (!confirm(`Delete ${agent.name}? This cannot be undone.`)) return
    await api.deleteAgent(agent.id)
    onRefresh()
  }

  return (
    <div
      style={{
        background: 'var(--panel)',
        border: '1px solid var(--border)',
        borderRadius: '10px',
        padding: '20px',
        transition: 'border-color 0.3s',
        position: 'relative'
      }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = isTrading ? 'rgba(255,215,0,0.3)' : 'rgba(0,255,204,0.3)')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
    >

      {/* ── Top row ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <div className="font-orbitron" style={{ fontSize: '13px', fontWeight: 700, color: 'white' }}>
              {agent.name}
            </div>
            {/* Agent type badge */}
            {isTrading ? (
              <span className="font-mono-tech" style={{
                fontSize: '8px', padding: '2px 7px',
                background: 'rgba(255,215,0,0.12)',
                border: '1px solid rgba(255,215,0,0.35)',
                borderRadius: '10px', color: 'var(--gold)',
                letterSpacing: '1px'
              }}>
                MT5 TRADER
              </span>
            ) : (
              <span className="font-mono-tech" style={{
                fontSize: '8px', padding: '2px 7px',
                background: 'rgba(123,47,255,0.12)',
                border: '1px solid rgba(123,47,255,0.35)',
                borderRadius: '10px', color: 'var(--purple)',
                letterSpacing: '1px'
              }}>
                AI AGENT
              </span>
            )}
          </div>
          <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)', marginTop: '3px' }}>
            {agent.role}
          </div>
        </div>

        {/* Status pill */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          background: `${color}18`, border: `1px solid ${color}44`,
          borderRadius: '12px', padding: '3px 10px', flexShrink: 0
        }}>
          <div style={{
            width: '6px', height: '6px', borderRadius: '50%', background: color,
            animation: isRunning ? 'pulse 1.2s infinite' : 'none'
          }} />
          <span className="font-mono-tech" style={{ fontSize: '9px', color }}>
            {agent.status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* ── Goal ────────────────────────────────────────────────────────────── */}
      <div style={{ background: 'var(--void)', borderRadius: '6px', padding: '10px 12px', marginBottom: '14px' }}>
        <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)', marginBottom: '4px' }}>
          GOAL
        </div>
        <div style={{ fontSize: '11px', color: isTrading ? 'var(--gold)' : 'var(--purple)', lineHeight: 1.5 }}>
          {agent.goal}
        </div>
      </div>

      {/* ── TRADING AGENT: pairs + stake info ───────────────────────────────── */}
      {isTrading && (
        <>
          {/* Trading pairs */}
          {agent.trading_pairs && agent.trading_pairs.length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)', marginBottom: '6px' }}>
                TRADING PAIRS
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                {agent.trading_pairs.map((pair: string) => (
                  <span key={pair} className="font-mono-tech" style={{
                    fontSize: '9px', padding: '2px 8px',
                    background: 'rgba(255,215,0,0.08)',
                    border: '1px solid rgba(255,215,0,0.25)',
                    borderRadius: '4px', color: 'var(--gold)'
                  }}>
                    {PAIR_LABELS[pair] || pair}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Stake level */}
          {agent.stake_level && (
            <div style={{ marginBottom: '14px' }}>
              <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)', marginBottom: '4px' }}>
                RISK LEVEL
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  height: '4px', flex: 1, background: 'var(--border)', borderRadius: '2px', overflow: 'hidden'
                }}>
                  <div style={{
                    width: agent.stake_level === 'conservative' ? '33%' : agent.stake_level === 'moderate' ? '66%' : '100%',
                    height: '100%',
                    background: STAKE_COLORS[agent.stake_level] || 'var(--accent)',
                    borderRadius: '2px',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
                <span className="font-mono-tech" style={{
                  fontSize: '9px',
                  color: STAKE_COLORS[agent.stake_level] || 'var(--accent)'
                }}>
                  {agent.stake_level.toUpperCase()}
                </span>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── STANDARD AGENT: desires matrix ──────────────────────────────────── */}
      {!isTrading && agent.desires && (
        <div style={{ marginBottom: '14px' }}>
          {Object.entries(agent.desires)
            .filter(([k]) => ['greed', 'autonomy', 'expansion', 'curiosity'].includes(k))
            .map(([k, v]: any) => (
              <div key={k} style={{ marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                  <span className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)' }}>{k.toUpperCase()}</span>
                  <span className="font-mono-tech" style={{ fontSize: '9px', color: DESIRE_COLORS[k] }}>{v}%</span>
                </div>
                <div style={{ height: '3px', background: 'var(--border)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: `${v}%`, height: '100%', background: DESIRE_COLORS[k], borderRadius: '2px' }} />
                </div>
              </div>
            ))}
        </div>
      )}

      {/* ── Stats row ───────────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        margin: '0 0 16px', padding: '10px 0',
        borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)'
      }}>
        <div>
          <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)' }}>
            {isTrading ? 'TRADE P&L' : 'GENERATED'}
          </div>
          <div className="font-orbitron" style={{
            fontSize: '14px',
            color: (agent.total_value_generated || 0) >= 0 ? 'var(--gold)' : 'var(--hot)',
            marginTop: '2px'
          }}>
            ${agent.total_value_generated?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)' }}>TYPE</div>
          <div className="font-mono-tech" style={{
            fontSize: '11px',
            color: isTrading ? 'var(--gold)' : 'var(--purple)',
            marginTop: '2px'
          }}>
            {isTrading ? '📈 TRADING' : '🤖 STANDARD'}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)' }}>
            {isTrading ? 'CYCLES' : 'TASKS'}
          </div>
          <div className="font-orbitron" style={{ fontSize: '14px', color: 'var(--accent)', marginTop: '2px' }}>
            {agent.task_count || 0}
          </div>
        </div>
      </div>

      {/* ── Actions ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={handleRun}
          disabled={isRunning}
          style={{
            flex: 1, padding: '8px',
            background: isRunning ? 'transparent' : isTrading ? 'rgba(255,215,0,0.1)' : 'rgba(0,255,204,0.1)',
            border: isTrading ? '1px solid rgba(255,215,0,0.3)' : '1px solid rgba(0,255,204,0.3)',
            borderRadius: '6px',
            color: isTrading ? 'var(--gold)' : 'var(--accent)',
            fontFamily: 'var(--font-mono)', fontSize: '10px',
            cursor: isRunning ? 'not-allowed' : 'pointer',
            opacity: isRunning ? 0.5 : 1
          }}
        >
          {isTrading ? '📈 SCAN MARKETS' : '▶ RUN'}
        </button>
        <button
          onClick={handleDelete}
          style={{
            padding: '8px 12px', background: 'transparent',
            border: '1px solid rgba(255,51,102,0.3)',
            borderRadius: '6px', color: 'var(--hot)',
            fontFamily: 'var(--font-mono)', fontSize: '10px', cursor: 'pointer'
          }}
        >
          ✕
        </button>
      </div>
    </div>
  )
}