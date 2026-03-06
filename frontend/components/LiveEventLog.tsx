// Step 24: Live event log
// frontend/components/LiveEventLog.tsx
'use client'
import { useEffect, useRef } from 'react'

// ── Event type → color ────────────────────────────────────────────────────────
const TYPE_COLORS: Record<string, string> = {
  // Standard agent events
  start:    'var(--accent)',
  revenue:  'var(--gold)',
  desire:   'var(--purple)',
  error:    'var(--hot)',
  portal:   'var(--purple)',
  mine:     'var(--gold)',
  conflict: 'var(--hot)',
  // Trading agent events
  trade:    'var(--gold)',    // trade placed
  scan:     'var(--accent)',  // scanning markets
  pnl:      'var(--gold)',    // P&L update
  wait:     'var(--dim)',     // waiting / no setup found
}

// ── Event type → icon ─────────────────────────────────────────────────────────
const TYPE_ICONS: Record<string, string> = {
  // Standard agent events
  start:    '◉',
  revenue:  '$',
  desire:   '◈',
  error:    '✕',
  portal:   '⟁',
  mine:     '◆',
  conflict: '⚡',
  // Trading agent events
  trade:    '📈',
  scan:     '🔍',
  pnl:      '💰',
  wait:     '⏸',
}

export default function LiveEventLog({ events }: { events: any[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  return (
    <div style={{ height: '320px', overflowY: 'auto', padding: '0' }}>
      {events.length === 0 && (
        <div
          className="font-mono-tech"
          style={{ color: 'var(--dim)', fontSize: '11px', padding: '24px', textAlign: 'center' }}
        >
          Waiting for agent activity...
        </div>
      )}

      {events.map((ev, i) => {
        const type      = ev.event_type || ev.type || 'event'
        const color     = TYPE_COLORS[type] || 'var(--dim)'
        const icon      = TYPE_ICONS[type]  || '·'
        const isTradeEv = ['trade', 'scan', 'pnl', 'wait'].includes(type)

        return (
          <div
            key={i}
            style={{
              display: 'flex', gap: '12px',
              padding: '10px 20px',
              borderBottom: '1px solid rgba(255,255,255,0.02)',
              alignItems: 'flex-start',
              animation: 'fadeIn 0.3s ease',
              // Subtle gold tint on trading events
              background: isTradeEv ? 'rgba(255,215,0,0.02)' : 'transparent'
            }}
          >
            {/* Timestamp */}
            <span
              className="font-mono-tech"
              style={{ fontSize: '9px', color: 'var(--dim)', whiteSpace: 'nowrap', paddingTop: '2px', minWidth: '60px' }}
            >
              {new Date(ev.created_at || Date.now()).toLocaleTimeString()}
            </span>

            {/* Event type badge */}
            <span
              className="font-mono-tech"
              style={{
                fontSize: '9px', padding: '2px 8px', borderRadius: '4px',
                whiteSpace: 'nowrap',
                background: `${color}18`,
                color,
                border: `1px solid ${color}33`,
                minWidth: '74px', textAlign: 'center'
              }}
            >
              {icon} {type.toUpperCase()}
            </span>

            {/* Message */}
            <span
              className="font-mono-tech"
              style={{ fontSize: '10px', color: 'var(--text)', flex: 1, lineHeight: 1.5 }}
            >
              {ev.message}
            </span>

            {/* Value — show for both positive revenue and negative P&L */}
            {ev.value != null && ev.value !== 0 && (
              <span
                className="font-orbitron"
                style={{
                  fontSize: '11px',
                  color: ev.value >= 0 ? 'var(--gold)' : 'var(--hot)',
                  whiteSpace: 'nowrap'
                }}
              >
                {ev.value >= 0 ? '+' : ''}${Math.abs(ev.value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            )}
          </div>
        )
      })}

      <div ref={bottomRef} />
    </div>
  )
}