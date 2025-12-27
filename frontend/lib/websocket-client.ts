import { config } from './config'

export type WebSocketMessage = {
  type: 'message' | 'error' | 'status' | 'stream_start' | 'stream_chunk' | 'stream_end'
  data?: unknown
  error?: string
  messageId?: string
  chatId?: string
}

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnecting' | 'disconnected' | 'error'

export type WebSocketEventCallback = (message: WebSocketMessage) => void
export type WebSocketStatusCallback = (status: WebSocketStatus) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private messageCallbacks: Set<WebSocketEventCallback> = new Set()
  private statusCallbacks: Set<WebSocketStatusCallback> = new Set()
  private status: WebSocketStatus = 'disconnected'
  private heartbeatInterval: NodeJS.Timeout | null = null
  private reconnectTimeout: NodeJS.Timeout | null = null

  /**
   * Get WebSocket URL from backend URL
   */
  private getWebSocketUrl(): string {
    const baseUrl = config.api.baseUrl
    // Convert http(s) to ws(s)
    const wsUrl = baseUrl.replace(/^http/, 'ws')
    return `${wsUrl}/ws`
  }

  /**
   * Connect to WebSocket server
   */
  async connect(token?: string): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      this.setStatus('connecting')
      
      const url = this.getWebSocketUrl()
      const wsUrl = token ? `${url}?token=${token}` : url
      
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        this.reconnectAttempts = 0
        this.setStatus('connected')
        this.startHeartbeat()
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.notifyMessageCallbacks(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = () => {
        // WebSocket endpoint not implemented on backend yet
        // Silently handle error to avoid console spam
        this.setStatus('error')
      }

      this.ws.onclose = () => {
        this.setStatus('disconnected')
        this.stopHeartbeat()
        // Don't attempt reconnect if backend doesn't support WebSocket
        // this.attemptReconnect(token)
      }
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error)
      this.setStatus('error')
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.setStatus('disconnecting')
    this.stopHeartbeat()
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.setStatus('disconnected')
  }

  /**
   * Send a message through WebSocket
   */
  send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message)
    }
  }

  /**
   * Subscribe to WebSocket messages
   */
  onMessage(callback: WebSocketEventCallback): () => void {
    this.messageCallbacks.add(callback)
    return () => {
      this.messageCallbacks.delete(callback)
    }
  }

  /**
   * Subscribe to WebSocket status changes
   */
  onStatusChange(callback: WebSocketStatusCallback): () => void {
    this.statusCallbacks.add(callback)
    // Immediately call with current status
    callback(this.status)
    return () => {
      this.statusCallbacks.delete(callback)
    }
  }

  /**
   * Get current connection status
   */
  getStatus(): WebSocketStatus {
    return this.status
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.status === 'connected' && this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * Set status and notify callbacks
   */
  private setStatus(status: WebSocketStatus): void {
    this.status = status
    this.statusCallbacks.forEach((callback) => callback(status))
  }

  /**
   * Notify message callbacks
   */
  private notifyMessageCallbacks(message: WebSocketMessage): void {
    this.messageCallbacks.forEach((callback) => callback(message))
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'status', data: 'ping' })
      }
    }, 30000) // Every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(token?: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    this.reconnectTimeout = setTimeout(() => {
      this.connect(token)
    }, delay)
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient()
