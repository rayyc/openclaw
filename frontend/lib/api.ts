// Step 14: API client
// frontend/lib/api.ts
import { useAuthStore } from './store'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface RequestOptions extends RequestInit {
  requiresAuth?: boolean
}

export async function apiCall(
  endpoint: string,
  options: RequestOptions = {}
): Promise<any> {
  const { requiresAuth = true, ...init } = options
  const headers = new Headers(init.headers || {})

  if (requiresAuth) {
    const token = useAuthStore.getState().token
    if (!token) throw new Error('Not authenticated')
    headers.set('Authorization', `Bearer ${token}`)
  }

  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_URL}${endpoint}`, { ...init, headers })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(error || `API error: ${response.status}`)
  }

  return response.json()
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const auth = {
  register: (email: string, password: string) =>
    apiCall('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      requiresAuth: false
    }),
  login: (email: string, password: string) =>
    apiCall('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      requiresAuth: false
    })
}

// ── Agents ────────────────────────────────────────────────────────────────────
export const agents = {
  // Standard agent — web search, email, SEO, Upwork, LinkedIn
  deploy: (
    name: string,
    role: string,
    goal: string,
    backstory: string,
    desires?: Record<string, number>
  ) =>
    apiCall('/agents/deploy', {
      method: 'POST',
      body: JSON.stringify({ name, role, goal, backstory, desires })
    }),

  // Trading agent — Deriv MT5 forex and commodities
  deployTrading: (payload: {
    name: string
    goal: string
    trading_pairs: string[]
    stake_level: string
  }) =>
    apiCall('/agents/deploy/trading', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),

  list:      ()            => apiCall('/agents/'),
  getEvents: (id: string)  => apiCall(`/agents/${id}/events`),
  run:       (id: string)  => apiCall(`/agents/${id}/run`, { method: 'POST' }),
  delete:    (id: string)  => apiCall(`/agents/${id}`,     { method: 'DELETE' })
}

// ── Billing ───────────────────────────────────────────────────────────────────
export const billing = {
  checkout: (tier: string) =>
    apiCall(`/billing/checkout/${tier}`, { method: 'POST' })
}

// ── Default aggregated API (legacy component imports) ─────────────────────────
const api = {
  register:    auth.register,
  login:       auth.login,

  deployAgent: (payload: {
    name: string
    role: string
    goal: string
    backstory: string
    desires?: Record<string, number>
  }) => agents.deploy(payload.name, payload.role, payload.goal, payload.backstory, payload.desires),

  deployTradingAgent: (payload: {
    name: string
    goal: string
    trading_pairs: string[]
    stake_level: string
  }) => agents.deployTrading(payload),

  listAgents:      agents.list,
  getAgentEvents:  agents.getEvents,
  runAgent:        (id: string) => agents.run(id),
  deleteAgent:     (id: string) => agents.delete(id),

  checkout: billing.checkout,
}

export default api