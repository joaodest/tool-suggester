import { AVAILABLE_TOOLS } from '../constants';
import { Tool } from '../types';
import { getWebSocketService, ConnectionStatus } from './websocketService';

// Mode: 'websocket' (default) or 'mock' (fallback)
let suggestionMode: 'websocket' | 'mock' = 'websocket';
let wsService = getWebSocketService();

/**
 * Get current suggestion mode.
 */
export const getSuggestionMode = (): 'websocket' | 'mock' => suggestionMode;

/**
 * Get connection status (only relevant for WebSocket mode).
 */
export const getConnectionStatus = (): ConnectionStatus => {
  return wsService.getStatus();
};

/**
 * Initialize the suggestion service.
 * Attempts WebSocket connection, falls back to mock if unavailable.
 */
export const initializeSuggestionService = async (): Promise<void> => {
  try {
    await wsService.connect();
    suggestionMode = 'websocket';
    console.log('[SuggestionService] Using WebSocket mode (Python engine)');
  } catch (error) {
    console.warn('[SuggestionService] WebSocket unavailable, using mock mode:', error);
    suggestionMode = 'mock';
  }
};

/**
 * Get tool suggestions based on user input.
 * Uses WebSocket if available, otherwise falls back to mock.
 */
export const getToolSuggestions = (input: string): Tool[] => {
  if (!input || input.trim().length < 2) return [];

  // In WebSocket mode, suggestions are received via callback
  // This function is used for mock mode only
  if (suggestionMode === 'websocket') {
    // WebSocket handles this asynchronously
    return [];
  }

  // Mock mode fallback (original implementation)
  const normalizedInput = input.toLowerCase();

  const matches = AVAILABLE_TOOLS.filter(tool => {
    return tool.keywords.some(keyword => normalizedInput.includes(keyword));
  });

  return Array.from(new Set(matches));
};

/**
 * Submit text for suggestions (WebSocket mode).
 */
export const submitText = (text: string): void => {
  if (suggestionMode === 'websocket') {
    wsService.submit(text);
  }
};

/**
 * Feed text delta for incremental suggestions (WebSocket mode).
 */
export const feedTextDelta = (delta: string): void => {
  if (suggestionMode === 'websocket') {
    wsService.feed(delta);
  }
};

/**
 * Reset suggestion session.
 */
export const resetSession = (): void => {
  if (suggestionMode === 'websocket') {
    wsService.reset();
  }
};

/**
 * Register callback for suggestions (WebSocket mode).
 */
export const onSuggestionsReceived = (callback: (suggestions: Tool[]) => void): void => {
  wsService.onSuggestionsReceived(callback);
};

/**
 * Register callback for connection status changes.
 */
export const onConnectionStatusChange = (callback: (status: ConnectionStatus) => void): void => {
  wsService.onConnectionStatusChange(callback);
};
