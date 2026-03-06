// Step 25: Main dashboard
// frontend/app/dashboard/page.tsx
'use client'
import { useEffect, useState, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { agents, billing } from '@/lib/api'
import { subscribeToAgentEvents } from '@/lib/websocket'
import AgentCard from '@/components/AgentCard'
import LiveEventLog from '@/components/LiveEventLog'
import DeployModal from '@/components/DeployModal'

const TIER_LIMITS: Record<string, number> = {
  free:      1,
  starter:   2,
  empire:    10,
  unlimited: 999,
  admin:     999
}

export default function Dashboard() {
  const { token, user, clearAuth } = useAuthStore()
  const router       = useRouter()
  const searchParams = useSearchParams()

  const [agentList, setAgentList]     = useState<any[]>([])
  const [events, setEvents]           = useState<any[]>([])
  const [showDeploy, setShowDeploy]   = useState(false)
  const [loading, setLoading]         = useState(true)
  const [wsConnected, setWsConnected] = useState(false)

  useEffect(() => {
    if (!token) { router.push('/'); return }
    loadAgents()
    setupWebSocket()
    if (searchParams.get('upgraded') === 'true') {
      alert('🎉 Upgrade successful! Your new agent slots are now active.')
    }
  }, [token, router, searchParams])

  async function loadAgents() {
    try {
      const data = await agents.list()
      setAgentList(data)
      const allEvents: any[] = []
      for (const agent of data) {
        const agentEvents = await agents.getEvents(agent.id)
        allEvents.push(...agentEvents)
      }
      allEvents.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      setEvents(allEvents.slice(0, 50))
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  function setupWebSocket() {
    if (!user?.id) return
    const ws = subscribeToAgentEvents(user.id, (event) => {
      setEvents(prev => [{ ...event, created_at: new Date().toISOString() }, ...prev].slice(0, 100))
      if (event.type === 'revenue') loadAgents()
    })
    ws.onopen  = () => setWsConnected(true)
    ws.onclose = () => setWsConnected(false)
    return () => ws.close()
  }

  // ── Derived stats ──────────────────────────────────────────────────────────
  const totalValue    = agentList.reduce((s, a) => s + (a.total_value_generated || 0), 0)
  const runningCount  = agentList.filter(a => a.status === 'running').length
  const tradingAgents = agentList.filter(a => a.agent_type === 'trading')
  const standardAgents = agentList.filter(a => a.agent_type !== 'trading')
  const limit         = TIER_LIMITS[user?.tier?.toLowerCase() || 'free'] ?? 999
  const isAdmin       = user?.tier?.toLowerCase() === 'admin'
  const atLimit       = agentList.length >= limit && !isAdmin

  async function handleUpgrade(tier: string) {
    const { checkout_url } = await billing.checkout(tier)
    window.location.href = checkout_url
  }

  function handleLogout() {
    clearAuth()
    router.push('/')
  }

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
      <span className="font-orbitron" style={{ color: 'var(--accent)', letterSpacing: '3px', fontSize: '14px' }}>
        INITIALIZING...
      </span>
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', padding: '0 24px 60px' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>

        {/* ── HEADER ──────────────────────────────────────────────────────── */}
        <header style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '24px 0 20px', borderBottom: '1px solid var(--border)', marginBottom: '28px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{ fontSize: '28px' }}>⚙</span>
            <div>
              <h1 className="font-orbitron" style={{ fontSize: '18px', fontWeight: 900, color: 'var(--accent)', letterSpacing: '4px' }}>
                OPENCLAW
              </h1>
              <span className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)', letterSpacing: '2px' }}>
                AGENT EMPIRE · {user?.email}
              </span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* WS status */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '5px 12px',
              background: wsConnected ? 'rgba(0,255,204,0.08)' : 'rgba(255,51,102,0.08)',
              border: `1px solid ${wsConnected ? 'rgba(0,255,204,0.2)' : 'rgba(255,51,102,0.2)'}`,
              borderRadius: '16px'
            }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: wsConnected ? 'var(--accent)' : 'var(--hot)' }} />
              <span className="font-mono-tech" style={{ fontSize: '10px', color: wsConnected ? 'var(--accent)' : 'var(--hot)' }}>
                {wsConnected ? 'LIVE' : 'OFFLINE'}
              </span>
            </div>

            {/* Tier badge */}
            <span className="font-mono-tech" style={{
              fontSize: '10px', color: 'var(--dim)', background: 'var(--panel)',
              border: '1px solid var(--border)', padding: '5px 12px', borderRadius: '16px'
            }}>
              {user?.tier?.toUpperCase() || 'FREE'}
            </span>

            {/* Admin badge */}
            {isAdmin && (
              <span className="font-mono-tech" style={{
                fontSize: '10px', color: 'var(--gold)',
                background: 'rgba(255,215,0,0.1)', border: '1px solid rgba(255,215,0,0.3)',
                padding: '5px 12px', borderRadius: '16px'
              }}>
                ADMIN
              </span>
            )}

            <button onClick={handleLogout} style={{
              background: 'none', border: '1px solid var(--border)', color: 'var(--dim)',
              padding: '5px 12px', borderRadius: '6px', fontFamily: 'var(--font-mono)',
              fontSize: '10px', cursor: 'pointer'
            }}>
              LOGOUT
            </button>
          </div>
        </header>

        {/* ── MONEY BANNER ────────────────────────────────────────────────── */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(255,215,0,0.05), rgba(123,47,255,0.08))',
          border: '1px solid rgba(255,215,0,0.2)', borderRadius: '12px',
          padding: '28px 36px', marginBottom: '24px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          flexWrap: 'wrap', gap: '20px'
        }}>
          <div>
            <div className="font-mono-tech" style={{ fontSize: '10px', color: 'var(--dim)', letterSpacing: '3px', marginBottom: '6px' }}>
              TOTAL VALUE GENERATED
            </div>
            <div className="font-orbitron" style={{ fontSize: '48px', fontWeight: 900, color: 'var(--gold)', textShadow: '0 0 30px rgba(255,215,0,0.3)' }}>
              ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px 32px' }}>
            {[
              { label: 'ACTIVE AGENTS',   val: `${runningCount} / ${agentList.length}`,       color: 'var(--accent)' },
              { label: 'TOTAL AGENTS',    val: `${agentList.length} / ${limit === 999 ? '∞' : limit}`, color: 'var(--text)' },
              { label: 'AI AGENTS',       val: standardAgents.length.toString(),               color: 'var(--purple)' },
              { label: 'TRADING AGENTS',  val: tradingAgents.length.toString(),                color: 'var(--gold)' },
              { label: 'TOTAL TASKS',     val: agentList.reduce((s, a) => s + (a.task_count || 0), 0).toString(), color: 'var(--accent)' },
              { label: 'PLAN',            val: (user?.tier || 'free').toUpperCase(),           color: 'var(--gold)' },
            ].map(s => (
              <div key={s.label} style={{ textAlign: 'right' }}>
                <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)' }}>{s.label}</div>
                <div className="font-orbitron" style={{ fontSize: '16px', color: s.color, marginTop: '2px' }}>{s.val}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ── AGENTS HEADER ───────────────────────────────────────────────── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <span className="font-orbitron" style={{ fontSize: '12px', letterSpacing: '3px' }}>AGENT ENTITIES</span>
          <div style={{ display: 'flex', gap: '10px' }}>
            {atLimit && (
              <button onClick={() => handleUpgrade('empire')} style={{
                padding: '8px 16px', background: 'rgba(255,215,0,0.1)',
                border: '1px solid rgba(255,215,0,0.3)', borderRadius: '6px',
                color: 'var(--gold)', fontFamily: 'var(--font-mono)', fontSize: '10px', cursor: 'pointer'
              }}>
                ↑ UPGRADE
              </button>
            )}
            <button
              onClick={() => setShowDeploy(true)}
              disabled={atLimit}
              style={{
                padding: '8px 16px',
                background: atLimit ? 'transparent' : 'rgba(0,255,204,0.1)',
                border: `1px solid ${atLimit ? 'var(--border)' : 'rgba(0,255,204,0.3)'}`,
                borderRadius: '6px',
                color: atLimit ? 'var(--dim)' : 'var(--accent)',
                fontFamily: 'var(--font-mono)', fontSize: '10px',
                cursor: atLimit ? 'not-allowed' : 'pointer'
              }}
            >
              ⊕ DEPLOY ENTITY
            </button>
          </div>
        </div>

        {/* ── AGENTS GRID ─────────────────────────────────────────────────── */}
        {agentList.length === 0 ? (
          <div style={{
            textAlign: 'center', padding: '60px', background: 'var(--panel)',
            border: '1px solid var(--border)', borderRadius: '12px', marginBottom: '24px'
          }}>
            <div style={{ fontSize: '40px', marginBottom: '16px' }}>⚙</div>
            <div className="font-orbitron" style={{ fontSize: '14px', letterSpacing: '3px', color: 'var(--dim)', marginBottom: '8px' }}>
              NO ENTITIES DEPLOYED
            </div>
            <div className="font-mono-tech" style={{ fontSize: '11px', color: 'var(--dim)', marginBottom: '20px' }}>
              Deploy an AI agent or a trading agent to begin
            </div>
            <button onClick={() => setShowDeploy(true)} style={{
              padding: '10px 24px',
              background: 'linear-gradient(135deg, var(--purple), var(--accent))',
              border: 'none', borderRadius: '6px', color: 'black',
              fontFamily: 'var(--font-orbitron)', fontSize: '11px',
              fontWeight: 700, letterSpacing: '2px', cursor: 'pointer'
            }}>
              ⊕ DEPLOY FIRST ENTITY
            </button>
          </div>
        ) : (
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '16px', marginBottom: '24px'
          }}>
            {agentList.map(a => <AgentCard key={a.id} agent={a} onRefresh={loadAgents} />)}
          </div>
        )}

        {/* ── EVENT LOG ───────────────────────────────────────────────────── */}
        <div style={{
          background: 'var(--panel)', border: '1px solid var(--border)',
          borderRadius: '12px', overflow: 'hidden', marginBottom: '24px'
        }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '16px 20px', borderBottom: '1px solid var(--border)'
          }}>
            <span className="font-orbitron" style={{ fontSize: '11px', letterSpacing: '3px' }}>LIVE EVENT STREAM</span>
            <span className="font-mono-tech" style={{
              fontSize: '10px', color: 'var(--accent)',
              background: 'rgba(0,255,204,0.08)', border: '1px solid rgba(0,255,204,0.2)',
              borderRadius: '4px', padding: '2px 8px'
            }}>
              {events.length} EVENTS
            </span>
          </div>
          <LiveEventLog events={events} />
        </div>

        {/* ── UPGRADE PLANS (free tier only) ──────────────────────────────── */}
        {user?.tier?.toLowerCase() === 'free' && (
          <div style={{
            background: 'var(--panel)', border: '1px solid var(--border)',
            borderRadius: '12px', padding: '28px'
          }}>
            <div className="font-orbitron" style={{ fontSize: '12px', letterSpacing: '3px', marginBottom: '20px', textAlign: 'center' }}>
              EXPAND YOUR EMPIRE
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
              {[
                { tier: 'starter',   name: 'STARTER',   price: '$29/mo',  agents: '2 agents',  color: 'var(--accent)' },
                { tier: 'empire',    name: 'EMPIRE',    price: '$99/mo',  agents: '10 agents', color: 'var(--gold)' },
                { tier: 'unlimited', name: 'UNLIMITED', price: '$299/mo', agents: '∞ agents',  color: 'var(--purple)' },
              ].map(p => (
                <div key={p.tier} style={{
                  textAlign: 'center', padding: '20px', background: 'var(--void)',
                  border: `1px solid ${p.color}33`, borderRadius: '8px'
                }}>
                  <div className="font-mono-tech" style={{ fontSize: '9px', color: p.color, letterSpacing: '2px', marginBottom: '8px' }}>{p.name}</div>
                  <div className="font-orbitron" style={{ fontSize: '22px', color: p.color, marginBottom: '4px' }}>{p.price}</div>
                  <div className="font-mono-tech" style={{ fontSize: '10px', color: 'var(--dim)', marginBottom: '16px' }}>{p.agents}</div>
                  <button onClick={() => handleUpgrade(p.tier)} style={{
                    width: '100%', padding: '8px',
                    background: `${p.color}18`, border: `1px solid ${p.color}44`,
                    borderRadius: '6px', color: p.color,
                    fontFamily: 'var(--font-mono)', fontSize: '10px', cursor: 'pointer'
                  }}>
                    UPGRADE →
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>

      {showDeploy && <DeployModal onClose={() => setShowDeploy(false)} onDeployed={loadAgents} />}
    </div>
  )
}