// Agent list page
'use client'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { useEffect } from 'react'

export default function AgentsPage() {
  const { token } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!token) {
      router.push('/')
    }
  }, [token, router])

  return (
    <div style={{ minHeight: '100vh', padding: '40px 24px', background: 'var(--void)' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h1 className="font-orbitron" style={{ fontSize: '24px', color: 'var(--accent)', letterSpacing: '3px', marginBottom: '20px' }}>
          AGENTS
        </h1>
        <div style={{ padding: '40px', textAlign: 'center', background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: '12px' }}>
          <p className="font-mono-tech" style={{ color: 'var(--dim)' }}>
            Navigate to the dashboard to manage your agents
          </p>
        </div>
      </div>
    </div>
  )
}