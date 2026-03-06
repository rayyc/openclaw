// Step 21: Landing page
// frontend/app/page.tsx
'use client'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useAuthStore } from '@/lib/store'

export default function Landing() {
  const router = useRouter()
  const { token } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState<'login' | 'register'>('register')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { setAuth } = useAuthStore()

  useEffect(() => {
    if (token) router.push('/dashboard')
  }, [token])

  async function handleSubmit() {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/${mode}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        }
      )
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setAuth(data.token, { 
        id: data.user_id, 
        email, 
        tier: data.tier || 'free',
        is_admin: data.is_admin || false 
      })
      router.push('/dashboard')
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', background: 'var(--void)', position: 'relative', overflow: 'hidden' }}>

      {/* Background glow */}
      <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: '600px', height: '600px', borderRadius: '50%', background: 'radial-gradient(ellipse, rgba(123,47,255,0.08) 0%, transparent 70%)', pointerEvents: 'none' }} />

      {/* Logo */}
      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚙</div>
        <h1 className="font-orbitron" style={{ fontSize: '32px', fontWeight: 900, color: 'var(--accent)', letterSpacing: '6px', textShadow: '0 0 30px rgba(0,255,204,0.4)', marginBottom: '8px' }}>
          OPENCLAW
        </h1>
        <p className="font-mono-tech" style={{ color: 'var(--dim)', fontSize: '11px', letterSpacing: '3px' }}>
          AUTONOMOUS AGENT EMPIRE
        </p>
        <p style={{ color: 'var(--text)', marginTop: '16px', fontSize: '16px', opacity: 0.7 }}>
          Deploy entities that <span style={{ color: 'var(--purple)' }}>want things</span>. Not automation —{' '}
          <span style={{ color: 'var(--accent)' }}>actual goals.</span>
        </p>
      </div>

      {/* Auth Box */}
      <div style={{ background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: '12px', padding: '36px', width: '100%', maxWidth: '400px', position: 'relative', zIndex: 1 }}>

        {/* Toggle */}
        <div style={{ display: 'flex', marginBottom: '28px', background: 'var(--void)', borderRadius: '8px', padding: '4px' }}>
          {(['register', 'login'] as const).map(m => (
            <button key={m} onClick={() => setMode(m)} style={{
              flex: 1, padding: '8px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: '11px', letterSpacing: '1px', transition: 'all 0.2s',
              background: mode === m ? 'var(--accent)' : 'transparent',
              color: mode === m ? 'black' : 'var(--dim)'
            }}>
              {m.toUpperCase()}
            </button>
          ))}
        </div>

        <input
          type="email"
          placeholder="EMAIL"
          value={email}
          onChange={e => setEmail(e.target.value)}
          style={{ width: '100%', padding: '12px 16px', marginBottom: '12px', background: 'var(--void)', border: '1px solid var(--border)', borderRadius: '6px', color: 'var(--text)', fontFamily: 'var(--font-mono)', fontSize: '12px', outline: 'none' }}
        />
        <input
          type="password"
          placeholder="PASSWORD"
          value={password}
          onChange={e => setPassword(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          style={{ width: '100%', padding: '12px 16px', marginBottom: '20px', background: 'var(--void)', border: '1px solid var(--border)', borderRadius: '6px', color: 'var(--text)', fontFamily: 'var(--font-mono)', fontSize: '12px', outline: 'none' }}
        />

        {error && (
          <p style={{ color: 'var(--hot)', fontFamily: 'var(--font-mono)', fontSize: '10px', marginBottom: '12px' }}>{error}</p>
        )}

        <button onClick={handleSubmit} disabled={loading} style={{
          width: '100%', padding: '14px', background: 'linear-gradient(135deg, var(--purple), var(--accent))', border: 'none', borderRadius: '6px', color: 'black', fontFamily: 'var(--font-orbitron)', fontSize: '12px', fontWeight: 700, letterSpacing: '2px', cursor: loading ? 'wait' : 'pointer', opacity: loading ? 0.7 : 1
        }}>
          {loading ? 'CONNECTING...' : mode === 'register' ? '⊕ CREATE EMPIRE' : '→ ENTER'}
        </button>
      </div>

      {/* Tiers preview */}
      <div style={{ display: 'flex', gap: '16px', marginTop: '40px', flexWrap: 'wrap', justifyContent: 'center' }}>
        {[
          { name: 'FREE', price: '$0', agents: '1 agent', color: 'var(--dim)' },
          { name: 'STARTER', price: '$29/mo', agents: '2 agents', color: 'var(--accent)' },
          { name: 'EMPIRE', price: '$99/mo', agents: '10 agents', color: 'var(--gold)' },
          { name: 'UNLIMITED', price: '$299/mo', agents: '∞ agents', color: 'var(--purple)' },
          { name: 'ADMIN', price: 'FREE', agents: '∞ agents', color: 'var(--hot)' },
        ].map(t => (
          <div key={t.name} style={{ background: 'var(--panel)', border: `1px solid ${t.color}22`, borderRadius: '8px', padding: '12px 20px', textAlign: 'center', minWidth: '100px' }}>
            <div className="font-mono-tech" style={{ fontSize: '9px', color: t.color, letterSpacing: '2px' }}>{t.name}</div>
            <div className="font-orbitron" style={{ fontSize: '16px', color: t.color, margin: '4px 0' }}>{t.price}</div>
            <div className="font-mono-tech" style={{ fontSize: '9px', color: 'var(--dim)' }}>{t.agents}</div>
          </div>
        ))}
      </div>
    </div>
  )
}