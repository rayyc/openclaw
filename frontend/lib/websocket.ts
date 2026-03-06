// Step 14: WebSocket client
// frontend/lib/websocket.ts
import { useAuthStore } from './store'

export function createWebSocketConnection(userId: string) {
  const token = useAuthStore.getState().token
  const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/events/${userId}`

  const ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('WebSocket connected')
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }

  ws.onclose = () => {
    console.log('WebSocket disconnected')
  }

  return ws
}

export function subscribeToAgentEvents(userId: string, onMessage: (event: any) => void) {
  const ws = createWebSocketConnection(userId)

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage(data)
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e)
    }
  }

  return ws
}