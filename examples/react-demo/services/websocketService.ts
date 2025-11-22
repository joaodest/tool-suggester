/**
 * WebSocket Service for Suggester Gateway
 *
 * Manages WebSocket connection to Python backend with automatic reconnection
 * and fallback to REST API.
 */

import { Tool } from '../types';

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

export interface SuggestionMessage {
  type: 'suggestions';
  suggestions: PythonSuggestion[];
  session_id: string;
}

export interface PythonSuggestion {
  id: string;
  kind: 'tool' | 'mcp';
  score: number;
  label: string;
  reason: string;
  arguments_template?: Record<string, any>;
  metadata?: {
    tags?: string[];
  };
}

interface WebSocketMessage {
  type: 'feed' | 'submit' | 'reset' | 'ping';
  session_id: string;
  text?: string;
  delta?: string;
  timestamp?: number;
}

class SuggesterWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private sessionId: string;
  private url: string;
  private onStatusChange?: (status: ConnectionStatus) => void;
  private onSuggestions?: (suggestions: Tool[]) => void;
  private status: ConnectionStatus = 'disconnected';

  constructor(
    url: string = 'ws://localhost:8000/ws/suggest',
    sessionId: string = 'react-session'
  ) {
    this.url = url;
    this.sessionId = sessionId;
  }

  setSessionId(sessionId: string) {
    this.sessionId = sessionId;
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  private setStatus(status: ConnectionStatus) {
    this.status = status;
    this.onStatusChange?.(status);
  }

  onConnectionStatusChange(callback: (status: ConnectionStatus) => void) {
    this.onStatusChange = callback;
  }

  onSuggestionsReceived(callback: (suggestions: Tool[]) => void) {
    this.onSuggestions = callback;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.setStatus('connecting');

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected to Suggester Gateway');
          this.reconnectAttempts = 0;
          this.setStatus('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          this.setStatus('error');
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('[WebSocket] Connection closed');
          this.setStatus('disconnected');
          this.attemptReconnect();
        };

      } catch (error) {
        this.setStatus('error');
        reject(error);
      }
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[WebSocket] Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('[WebSocket] Reconnection failed:', error);
      });
    }, delay);
  }

  private handleMessage(message: any) {
    if (message.type === 'suggestions') {
      const suggestions = this.convertPythonSuggestions(message.suggestions);
      this.onSuggestions?.(suggestions);
    } else if (message.type === 'pong') {
      // Health check response
      console.log('[WebSocket] Pong received');
    } else if (message.type === 'error') {
      console.error('[WebSocket] Server error:', message.error);
    }
  }

  private convertPythonSuggestions(pythonSuggestions: PythonSuggestion[]): Tool[] {
    return pythonSuggestions.map((sugg) => {
      // Extract category from tags or infer from kind
      const tags = sugg.metadata?.tags || [];
      let category: Tool['category'] = 'utility';

      if (tags.includes('data') || tags.includes('io')) {
        category = 'data';
      } else if (tags.includes('communication') || tags.includes('email')) {
        category = 'communication';
      } else if (tags.includes('system') || tags.includes('database')) {
        category = 'system';
      }

      // Extract keywords from reason field (e.g., "export: keywords; csv: keywords")
      const keywords: string[] = [];
      if (sugg.reason) {
        const parts = sugg.reason.split(';');
        parts.forEach(part => {
          const [term] = part.split(':');
          if (term) {
            keywords.push(term.trim());
          }
        });
      }

      return {
        id: sugg.id,
        name: sugg.label || sugg.id,
        description: `Score: ${sugg.score.toFixed(2)} | ${sugg.reason}`,
        keywords: keywords,
        category: category
      };
    });
  }

  private send(message: WebSocketMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Cannot send message: not connected');
    }
  }

  feed(delta: string) {
    this.send({
      type: 'feed',
      session_id: this.sessionId,
      delta: delta
    });
  }

  submit(text: string) {
    this.send({
      type: 'submit',
      session_id: this.sessionId,
      text: text
    });
  }

  reset() {
    this.send({
      type: 'reset',
      session_id: this.sessionId
    });
  }

  ping() {
    this.send({
      type: 'ping',
      session_id: this.sessionId,
      timestamp: Date.now()
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setStatus('disconnected');
  }
}

// Singleton instance
let wsInstance: SuggesterWebSocket | null = null;

export function getWebSocketService(): SuggesterWebSocket {
  if (!wsInstance) {
    wsInstance = new SuggesterWebSocket();
  }
  return wsInstance;
}

export async function connectToSuggester(): Promise<SuggesterWebSocket> {
  const ws = getWebSocketService();
  await ws.connect();
  return ws;
}
