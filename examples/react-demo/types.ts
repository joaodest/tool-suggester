export interface Tool {
  id: string;
  name: string;
  description: string;
  keywords: string[];
  category: 'data' | 'communication' | 'utility' | 'system';
  score?: number;  // Score from Python engine
  reason?: string;  // Match explanation from Python engine
  kind?: 'tool' | 'mcp';  // Tool type
  metadata?: {
    tags?: string[];
    [key: string]: any;
  };
}

export interface Message {
  id: string;
  role: 'user' | 'model';
  text: string;
  timestamp: number;
  isThinking?: boolean;
}

export enum SuggestionState {
  IDLE = 'IDLE',
  SUGGESTING = 'SUGGESTING',
  HIDDEN = 'HIDDEN'
}

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

export type SuggestionMode = 'websocket' | 'mock';

export interface EngineConfig {
  top_k: number;
  max_intents: number;
  min_score: number;
  combine_strategy: 'max' | 'sum';
  intent_separator_tokens: string[] | null;
  locales: string[];
}

export interface ConfigResponse {
  config: EngineConfig;
  status: string;
  message?: string;
}