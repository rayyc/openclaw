// Step 19: Zustand auth store
// frontend/lib/store.ts
import { create } from 'zustand'

export interface User {
  id: string
  email: string
  tier: 'free' | 'starter' | 'empire' | 'unlimited' | 'admin'
  is_admin?: boolean
}

export interface AuthState {
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: typeof window !== 'undefined' ? localStorage.getItem('token') : null,
  user: typeof window !== 'undefined' ? (() => {
    const stored = localStorage.getItem('user')
    return stored ? JSON.parse(stored) : null
  })() : null,
  setAuth: (token: string, user: User) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ token, user })
  },
  clearAuth: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ token: null, user: null })
  }
}))