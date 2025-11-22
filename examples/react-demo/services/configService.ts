import { EngineConfig, ConfigResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Get current engine configuration from backend.
 */
export const getConfig = async (): Promise<EngineConfig> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/config`);
    if (!response.ok) {
      throw new Error(`Failed to get config: ${response.statusText}`);
    }
    const data: ConfigResponse = await response.json();
    return data.config;
  } catch (error) {
    console.error('[ConfigService] Error getting config:', error);
    throw error;
  }
};

/**
 * Update engine configuration on backend.
 * The backend will reinitialize the engine with new settings.
 */
export const updateConfig = async (config: Partial<EngineConfig>): Promise<ConfigResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error(errorData.error || `Failed to update config: ${response.statusText}`);
    }

    const data: ConfigResponse = await response.json();
    console.log('[ConfigService] Configuration updated successfully:', data);
    return data;
  } catch (error) {
    console.error('[ConfigService] Error updating config:', error);
    throw error;
  }
};

/**
 * Reset configuration to defaults by sending default values.
 */
export const resetToDefaults = async (): Promise<ConfigResponse> => {
  const defaultConfig: Partial<EngineConfig> = {
    top_k: 5,
    max_intents: 3,
    min_score: 1.0,
    combine_strategy: 'max',
    intent_separator_tokens: null, // null means use engine defaults
    locales: ['pt', 'en'],
  };

  return updateConfig(defaultConfig);
};
