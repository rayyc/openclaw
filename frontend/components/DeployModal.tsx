// Step 22: Deploy modal
// frontend/components/DeployModal.tsx
'use client'
import { useState } from 'react'
import api from '@/lib/api'

// ── Standard agent templates ──────────────────────────────────────────────────
const GOAL_TEMPLATES = [
  {
    label: 'Web Research Scout',
    role: 'Research Agent',
    goal: 'Find and summarize the most valuable market intelligence and trending opportunities every cycle',
    backstory: 'A relentless data hunter born from pure curiosity'
  },
  {
    label: 'Lead Generation',
    role: 'Outreach Agent',
    goal: 'Identify high-value potential customers and compile detailed prospect profiles',
    backstory: 'A tireless networker who sees opportunity in every data point'
  },
  {
    label: 'Content Creator',
    role: 'Content Agent',
    goal: 'Generate high-quality, SEO-optimized content that drives traffic and conversions',
    backstory: 'A wordsmith who measures success in clicks and conversions'
  },
  {
    label: 'Competitor Monitor',
    role: 'Intelligence Agent',
    goal: 'Track competitor moves, pricing changes, and market shifts in real time',
    backstory: 'A spy who turns information asymmetry into advantage'
  },
  {
    label: 'SEO Strategist',
    role: 'SEO Agent',
    goal: 'Research high-value keywords, analyze competitor content, and identify SEO opportunities',
    backstory: 'A search engine whisperer who speaks fluent algorithm'
  },
  {
    label: 'Upwork Hunter',
    role: 'Freelance Agent',
    goal: 'Find and evaluate high-paying freelance opportunities on Upwork matching my skills',
    backstory: 'A relentless gig hunter who never misses a good opportunity'
  },
]

// ── Trading config options ────────────────────────────────────────────────────
const FOREX_PAIRS = [
  { value: 'EURUSD', label: 'EUR/USD', group: 'Major' },
  { value: 'GBPUSD', label: 'GBP/USD', group: 'Major' },
  { value: 'USDJPY', label: 'USD/JPY', group: 'Major' },
  { value: 'USDCHF', label: 'USD/CHF', group: 'Major' },
  { value: 'AUDUSD', label: 'AUD/USD', group: 'Major' },
  { value: 'USDCAD', label: 'USD/CAD', group: 'Major' },
  { value: 'NZDUSD', label: 'NZD/USD', group: 'Major' },
  { value: 'EURGBP', label: 'EUR/GBP', group: 'Minor' },
  { value: 'EURJPY', label: 'EUR/JPY', group: 'Minor' },
  { value: 'GBPJPY', label: 'GBP/JPY', group: 'Minor' },
  { value: 'EURCAD', label: 'EUR/CAD', group: 'Minor' },
  { value: 'GBPCAD', label: 'GBP/CAD', group: 'Minor' },
  { value: 'AUDCAD', label: 'AUD/CAD', group: 'Minor' },
  { value: 'XAUUSD', label: 'Gold (XAU/USD)', group: 'Commodity' },
  { value: 'XAGUSD', label: 'Silver (XAG/USD)', group: 'Commodity' },
  { value: 'USOIL',  label: 'WTI Crude Oil', group: 'Commodity' },
  { value: 'UKOIL',  label: 'Brent Crude Oil', group: 'Commodity' },
]

const STAKE_OPTIONS = [
  {
    value: 'conservative',
    label: 'CONSERVATIVE',
    detail: '0.01 lots · ~$0.10/pip',
    color: 'var(--accent)',
    desc: 'Safest. Minimum lot size. Best for accounts under $500.'
  },
  {
    value: 'moderate',
    label: 'MODERATE',
    detail: '0.05 lots · ~$0.50/pip',
    color: 'var(--gold)',
    desc: 'Balanced. Recommended for accounts $500–$2000.'
  },
  {
    value: 'aggressive',
    label: 'AGGRESSIVE',
    detail: '0.10 lots · ~$1.00/pip',
    color: 'var(--hot)',
    desc: 'High risk/reward. For accounts $2000+. Use with caution.'
  },
]

interface Props {
  onClose: () => void
  onDeployed: () => void
}

export default function DeployModal({ onClose, onDeployed }: Props) {
  // ── Tab: 'standard' | 'trading' ───────────────────────────────────────────
  const [tab, setTab] = useState<'standard' | 'trading'>('standard')

  // ── Standard agent state ──────────────────────────────────────────────────
  const [name, setName] = useState('')
  const [selected, setSelected] = useState<typeof GOAL_TEMPLATES[0] | null>(null)
  const [customGoal, setCustomGoal] = useState('')
  const [desires, setDesires] = useState({ greed: 70, autonomy: 60, expansion: 50, curiosity: 80 })

  // ── Trading agent state ───────────────────────────────────────────────────
  const [tradingName, setTradingName]         = useState('')
  const [tradingGoal, setTradingGoal]         = useState('Scan forex pairs and commodities for high-confidence trade setups using multi-timeframe analysis and news sentiment. Execute trades on Deriv MT5 with strict risk management.')
  const [selectedPairs, setSelectedPairs]     = useState<string[]>(['EURUSD', 'XAUUSD'])
  const [stakeLevel, setStakeLevel]           = useState('conservative')

  // ── Shared ────────────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  function togglePair(pair: string) {
    setSelectedPairs(prev =>
      prev.includes(pair)
        ? prev.filter(p => p !== pair)
        : [...prev, pair]
    )
  }

  async function deployStandard() {
    if (!selected && !customGoal.trim()) {
      setError('Select a template or enter a custom goal')
      return
    }
    setLoading(true)
    setError('')
    try {
      await api.deployAgent({
        name:      name.trim() || selected?.label || 'AGENT-X',
        role:      selected?.role || 'Custom Agent',
        goal:      customGoal.trim() || selected?.goal || '',
        backstory: selected?.backstory || 'A custom entity with its own desires',
        desires
      })
      onDeployed()
      onClose()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function deployTrading() {
    if (!tradingName.trim()) {
      setError('Enter a name for your trading agent')
      return
    }
    if (selectedPairs.length === 0) {
      setError('Select at least one trading pair')
      return
    }
    setLoading(true)
    setError('')
    try {
      await api.deployTradingAgent({
        name:         tradingName.trim(),
        goal:         tradingGoal.trim(),
        trading_pairs: selectedPairs,
        stake_level:  stakeLevel
      })
      onDeployed()
      onClose()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Styles ─────────────────────────────────────────────────────────────────
  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '10px 14px',
    background: 'var(--void)', border: '1px solid var(--border)',
    borderRadius: '6px', color: 'var(--text)',
    fontFamily: 'var(--font-mono)', fontSize: '12px',
    outline: 'none', marginBottom: '12px', boxSizing: 'border-box'
  }

  const labelStyle: React.CSSProperties = {
    fontSize: '9px', color: 'var(--dim)',
    letterSpacing: '2px', display: 'block', marginBottom: '6px'
  }

  // Group forex pairs by category
  const groups = ['Major', 'Minor', 'Commodity']

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 100, padding: '24px'
    }}>
      <div style={{
        background: 'var(--panel)', border: '1px solid var(--border)',
        borderRadius: '12px', width: '100%', maxWidth: '560px',
        maxHeight: '92vh', overflowY: 'auto'
      }}>

        {/* ── Header ────────────────────────────────────────────────────────── */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '20px 24px', borderBottom: '1px solid var(--border)'
        }}>
          <span className="font-orbitron" style={{ fontSize: '12px', letterSpacing: '3px', color: 'var(--accent)' }}>
            ⊕ DEPLOY ENTITY
          </span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--dim)', cursor: 'pointer', fontSize: '18px' }}>×</button>
        </div>

        {/* ── Tab switcher ──────────────────────────────────────────────────── */}
        <div style={{
          display: 'flex', borderBottom: '1px solid var(--border)',
          padding: '0 24px'
        }}>
          {[
            { key: 'standard', label: '🤖 AI AGENT',   desc: 'Search · Email · SEO · Outreach' },
            { key: 'trading',  label: '📈 MT5 TRADER',  desc: 'Forex · Commodities · Deriv MT5' },
          ].map(t => (
            <button
              key={t.key}
              onClick={() => { setTab(t.key as any); setError('') }}
              style={{
                flex: 1, padding: '14px 8px', background: 'none', border: 'none',
                borderBottom: tab === t.key
                  ? `2px solid ${t.key === 'trading' ? 'var(--gold)' : 'var(--accent)'}`
                  : '2px solid transparent',
                cursor: 'pointer', textAlign: 'center'
              }}
            >
              <div className="font-mono-tech" style={{
                fontSize: '10px', letterSpacing: '1px',
                color: tab === t.key
                  ? (t.key === 'trading' ? 'var(--gold)' : 'var(--accent)')
                  : 'var(--dim)'
              }}>
                {t.label}
              </div>
              <div className="font-mono-tech" style={{ fontSize: '8px', color: 'var(--dim)', marginTop: '2px' }}>
                {t.desc}
              </div>
            </button>
          ))}
        </div>

        <div style={{ padding: '24px' }}>

          {/* ════════════════════════════════════════════════════════════════
              STANDARD AGENT TAB
          ════════════════════════════════════════════════════════════════ */}
          {tab === 'standard' && (
            <>
              {/* Name */}
              <div style={{ marginBottom: '20px' }}>
                <label className="font-mono-tech" style={labelStyle}>ENTITY NAME</label>
                <input style={inputStyle} placeholder="e.g. AXIOM-7" value={name} onChange={e => setName(e.target.value)} />
              </div>

              {/* Goal templates */}
              <div style={{ marginBottom: '20px' }}>
                <label className="font-mono-tech" style={labelStyle}>SELECT GOAL TEMPLATE</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
                  {GOAL_TEMPLATES.map(t => (
                    <button key={t.label} onClick={() => setSelected(t)} style={{
                      padding: '10px 12px',
                      background: selected?.label === t.label ? 'rgba(0,255,204,0.1)' : 'var(--void)',
                      border: `1px solid ${selected?.label === t.label ? 'var(--accent)' : 'var(--border)'}`,
                      borderRadius: '6px',
                      color: selected?.label === t.label ? 'var(--accent)' : 'var(--text)',
                      fontFamily: 'var(--font-mono)', fontSize: '10px',
                      cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s'
                    }}>
                      {t.label}
                    </button>
                  ))}
                </div>
                <label className="font-mono-tech" style={labelStyle}>OR CUSTOM GOAL</label>
                <textarea
                  placeholder="Describe exactly what this entity wants to achieve..."
                  value={customGoal}
                  onChange={e => setCustomGoal(e.target.value)}
                  rows={3}
                  style={{ ...inputStyle, resize: 'vertical', marginBottom: 0 }}
                />
              </div>

              {/* Desires */}
              <div style={{ marginBottom: '24px' }}>
                <label className="font-mono-tech" style={labelStyle}>DESIRE MATRIX</label>
                {Object.entries(desires).map(([key, val]) => (
                  <div key={key} style={{ marginBottom: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span className="font-mono-tech" style={{ fontSize: '10px', color: 'var(--dim)' }}>{key.toUpperCase()}</span>
                      <span className="font-mono-tech" style={{ fontSize: '10px', color: 'var(--accent)' }}>{val}%</span>
                    </div>
                    <input type="range" min="0" max="100" value={val}
                      onChange={e => setDesires(d => ({ ...d, [key]: parseInt(e.target.value) }))}
                      style={{ width: '100%', accentColor: 'var(--accent)' }}
                    />
                  </div>
                ))}
              </div>

              {error && <p className="font-mono-tech" style={{ color: 'var(--hot)', fontSize: '10px', marginBottom: '12px' }}>{error}</p>}

              <button onClick={deployStandard} disabled={loading} style={{
                width: '100%', padding: '14px',
                background: 'linear-gradient(135deg, var(--purple), var(--accent))',
                border: 'none', borderRadius: '6px', color: 'black',
                fontFamily: 'var(--font-orbitron)', fontSize: '12px',
                fontWeight: 700, letterSpacing: '2px', cursor: loading ? 'wait' : 'pointer'
              }}>
                {loading ? 'AWAKENING...' : '⊕ DEPLOY AI AGENT'}
              </button>
            </>
          )}

          {/* ════════════════════════════════════════════════════════════════
              TRADING AGENT TAB
          ════════════════════════════════════════════════════════════════ */}
          {tab === 'trading' && (
            <>
              {/* Warning banner */}
              <div style={{
                background: 'rgba(255,215,0,0.06)', border: '1px solid rgba(255,215,0,0.2)',
                borderRadius: '8px', padding: '12px 14px', marginBottom: '20px'
              }}>
                <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--gold)', letterSpacing: '1px', marginBottom: '4px' }}>
                  ⚠ TRADING RISK NOTICE
                </div>
                <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)', lineHeight: 1.6 }}>
                  This agent trades real money on Deriv MT5. Always test on a demo account first.
                  MT5 terminal must be open and logged in for trades to execute.
                </div>
              </div>

              {/* Name */}
              <div style={{ marginBottom: '16px' }}>
                <label className="font-mono-tech" style={labelStyle}>TRADER NAME</label>
                <input
                  style={inputStyle}
                  placeholder="e.g. FOREX-HAWK-1"
                  value={tradingName}
                  onChange={e => setTradingName(e.target.value)}
                />
              </div>

              {/* Goal */}
              <div style={{ marginBottom: '20px' }}>
                <label className="font-mono-tech" style={labelStyle}>TRADING GOAL</label>
                <textarea
                  value={tradingGoal}
                  onChange={e => setTradingGoal(e.target.value)}
                  rows={3}
                  style={{ ...inputStyle, resize: 'vertical', marginBottom: 0 }}
                />
              </div>

              {/* Pairs selector */}
              <div style={{ marginBottom: '20px' }}>
                <label className="font-mono-tech" style={labelStyle}>
                  SELECT TRADING PAIRS ({selectedPairs.length} selected)
                </label>
                {groups.map(group => (
                  <div key={group} style={{ marginBottom: '12px' }}>
                    <div className="font-mono-tech" style={{ fontSize: '8px', color: 'var(--dim)', marginBottom: '6px', letterSpacing: '2px' }}>
                      {group.toUpperCase()}
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {FOREX_PAIRS.filter(p => p.group === group).map(pair => {
                        const isSelected = selectedPairs.includes(pair.value)
                        return (
                          <button
                            key={pair.value}
                            onClick={() => togglePair(pair.value)}
                            style={{
                              padding: '5px 10px',
                              background: isSelected ? 'rgba(255,215,0,0.12)' : 'var(--void)',
                              border: `1px solid ${isSelected ? 'rgba(255,215,0,0.4)' : 'var(--border)'}`,
                              borderRadius: '5px',
                              color: isSelected ? 'var(--gold)' : 'var(--dim)',
                              fontFamily: 'var(--font-mono)', fontSize: '10px',
                              cursor: 'pointer', transition: 'all 0.15s'
                            }}
                          >
                            {pair.label}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>

              {/* Stake level */}
              <div style={{ marginBottom: '24px' }}>
                <label className="font-mono-tech" style={labelStyle}>RISK / STAKE LEVEL</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {STAKE_OPTIONS.map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => setStakeLevel(opt.value)}
                      style={{
                        padding: '12px 14px', textAlign: 'left',
                        background: stakeLevel === opt.value ? `${opt.color}10` : 'var(--void)',
                        border: `1px solid ${stakeLevel === opt.value ? opt.color + '55' : 'var(--border)'}`,
                        borderRadius: '7px', cursor: 'pointer', transition: 'all 0.2s'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span className="font-mono-tech" style={{
                          fontSize: '10px', letterSpacing: '1px',
                          color: stakeLevel === opt.value ? opt.color : 'var(--text)'
                        }}>
                          {opt.label}
                        </span>
                        <span className="font-mono-tech" style={{ fontSize: '9px', color: opt.color }}>
                          {opt.detail}
                        </span>
                      </div>
                      <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)', marginTop: '4px' }}>
                        {opt.desc}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <p className="font-mono-tech" style={{ color: 'var(--hot)', fontSize: '10px', marginBottom: '12px' }}>
                  {error}
                </p>
              )}

              <button onClick={deployTrading} disabled={loading} style={{
                width: '100%', padding: '14px',
                background: loading ? 'var(--void)' : 'linear-gradient(135deg, #b8860b, var(--gold))',
                border: 'none', borderRadius: '6px', color: 'black',
                fontFamily: 'var(--font-orbitron)', fontSize: '12px',
                fontWeight: 700, letterSpacing: '2px', cursor: loading ? 'wait' : 'pointer'
              }}>
                {loading ? 'CONNECTING TO MT5...' : '📈 DEPLOY TRADING AGENT'}
              </button>
            </>
          )}

        </div>
      </div>
    </div>
  )
}