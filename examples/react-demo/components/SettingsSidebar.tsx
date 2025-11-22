import React, { useState, useEffect } from 'react';
import { EngineConfig } from '../types';
import { getConfig, updateConfig, resetToDefaults } from '../services/configService';

interface SettingsSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsSidebar: React.FC<SettingsSidebarProps> = ({ isOpen, onClose }) => {
  const [config, setConfig] = useState<EngineConfig>({
    top_k: 5,
    max_intents: 3,
    min_score: 1.0,
    combine_strategy: 'max',
    intent_separator_tokens: null,
    locales: ['pt', 'en'],
  });
  const [separatorText, setSeparatorText] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Load current config when sidebar opens
  useEffect(() => {
    if (isOpen) {
      loadConfig();
    }
  }, [isOpen]);

  const loadConfig = async () => {
    setIsLoading(true);
    try {
      const currentConfig = await getConfig();
      setConfig(currentConfig);

      // Convert separator tokens to comma-separated string for display
      if (currentConfig.intent_separator_tokens) {
        setSeparatorText(currentConfig.intent_separator_tokens.join(', '));
      } else {
        setSeparatorText('');
      }
    } catch (error) {
      showFeedback('error', 'Failed to load configuration');
      console.error('Error loading config:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const showFeedback = (type: 'success' | 'error', text: string) => {
    setFeedbackMessage({ type, text });
    setTimeout(() => setFeedbackMessage(null), 3000);
  };

  const handleApply = async () => {
    setIsSaving(true);
    try {
      // Parse separator tokens
      const separatorTokens = separatorText.trim()
        ? separatorText.split(',').map(t => t.trim()).filter(t => t)
        : null;

      const updatedConfig: Partial<EngineConfig> = {
        ...config,
        intent_separator_tokens: separatorTokens,
      };

      await updateConfig(updatedConfig);
      showFeedback('success', 'Configuration applied successfully!');
    } catch (error) {
      showFeedback('error', error instanceof Error ? error.message : 'Failed to update configuration');
      console.error('Error updating config:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('Reset all settings to defaults?')) return;

    setIsSaving(true);
    try {
      const response = await resetToDefaults();
      setConfig(response.config);
      setSeparatorText('');
      showFeedback('success', 'Reset to defaults successfully!');
    } catch (error) {
      showFeedback('error', 'Failed to reset configuration');
      console.error('Error resetting config:', error);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Sidebar */}
      <div className="fixed top-0 right-0 h-full w-full max-w-md bg-slate-900 shadow-2xl z-50 overflow-y-auto border-l border-slate-700">
        <div className="p-6">

          {/* Header */}
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-700">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-white">
                  <path fillRule="evenodd" d="M11.078 2.25c-.917 0-1.699.663-1.85 1.567L9.05 4.889c-.02.12-.115.26-.297.348a7.493 7.493 0 00-.986.57c-.166.115-.334.126-.45.083L6.3 5.508a1.875 1.875 0 00-2.282.819l-.922 1.597a1.875 1.875 0 00.432 2.385l.84.692c.095.078.17.229.154.43a7.598 7.598 0 000 1.139c.015.2-.059.352-.153.43l-.841.692a1.875 1.875 0 00-.432 2.385l.922 1.597a1.875 1.875 0 002.282.818l1.019-.382c.115-.043.283-.031.45.082.312.214.641.405.985.57.182.088.277.228.297.35l.178 1.071c.151.904.933 1.567 1.85 1.567h1.844c.916 0 1.699-.663 1.85-1.567l.178-1.072c.02-.12.114-.26.297-.349.344-.165.673-.356.985-.57.167-.114.335-.125.45-.082l1.02.382a1.875 1.875 0 002.28-.819l.923-1.597a1.875 1.875 0 00-.432-2.385l-.84-.692c-.095-.078-.17-.229-.154-.43a7.614 7.614 0 000-1.139c-.016-.2.059-.352.153-.43l.84-.692c.708-.582.891-1.59.433-2.385l-.922-1.597a1.875 1.875 0 00-2.282-.818l-1.02.382c-.114.043-.282.031-.449-.083a7.49 7.49 0 00-.985-.57c-.183-.087-.277-.227-.297-.348l-.179-1.072a1.875 1.875 0 00-1.85-1.567h-1.843zM12 15.75a3.75 3.75 0 100-7.5 3.75 3.75 0 000 7.5z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Engine Settings</h2>
                <p className="text-xs text-slate-400">Configure backend parameters</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-slate-400">
                <path fillRule="evenodd" d="M5.47 5.47a.75.75 0 011.06 0L12 10.94l5.47-5.47a.75.75 0 111.06 1.06L13.06 12l5.47 5.47a.75.75 0 11-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 01-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 010-1.06z" clipRule="evenodd" />
              </svg>
            </button>
          </div>

          {/* Feedback Message */}
          {feedbackMessage && (
            <div className={`mb-4 p-3 rounded-lg ${
              feedbackMessage.type === 'success'
                ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                : 'bg-red-500/10 border border-red-500/20 text-red-400'
            }`}>
              <p className="text-sm">{feedbackMessage.text}</p>
            </div>
          )}

          {/* Loading State */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <svg className="animate-spin h-8 w-8 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          ) : (
            <>
              {/* Settings Form */}
              <div className="space-y-6">

                {/* Top K */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Top K Results
                    <span className="ml-2 text-xs text-slate-500">(1-20)</span>
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={config.top_k}
                    onChange={(e) => setConfig({ ...config, top_k: parseInt(e.target.value) || 1 })}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <p className="mt-1 text-xs text-slate-500">Maximum number of suggestions to return</p>
                </div>

                {/* Max Intents */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Max Intents
                    <span className="ml-2 text-xs text-slate-500">(1-10)</span>
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={config.max_intents}
                    onChange={(e) => setConfig({ ...config, max_intents: parseInt(e.target.value) || 1 })}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <p className="mt-1 text-xs text-slate-500">Maximum number of intents to detect in input</p>
                </div>

                {/* Min Score */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Min Score
                    <span className="ml-2 text-xs text-slate-500">(≥ 0.0)</span>
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={config.min_score}
                    onChange={(e) => setConfig({ ...config, min_score: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <p className="mt-1 text-xs text-slate-500">Minimum score threshold for suggestions</p>
                </div>

                {/* Combine Strategy */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Combine Strategy
                  </label>
                  <select
                    value={config.combine_strategy}
                    onChange={(e) => setConfig({ ...config, combine_strategy: e.target.value as 'max' | 'sum' })}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="max">Max</option>
                    <option value="sum">Sum</option>
                  </select>
                  <p className="mt-1 text-xs text-slate-500">How to combine scores from multiple intent windows</p>
                </div>

                {/* Intent Separator Tokens */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Intent Separator Tokens
                  </label>
                  <textarea
                    value={separatorText}
                    onChange={(e) => setSeparatorText(e.target.value)}
                    placeholder="e, and, then, also, depois (leave empty for defaults)"
                    rows={3}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                  />
                  <p className="mt-1 text-xs text-slate-500">Comma-separated tokens that separate intents</p>
                </div>

              </div>

              {/* Action Buttons */}
              <div className="mt-8 flex gap-3">
                <button
                  onClick={handleApply}
                  disabled={isSaving}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 text-white font-medium py-3 px-4 rounded-lg transition-colors shadow-lg shadow-indigo-500/20"
                >
                  {isSaving ? 'Applying...' : 'Apply Changes'}
                </button>
                <button
                  onClick={handleReset}
                  disabled={isSaving}
                  className="px-4 py-3 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-700/50 text-slate-300 font-medium rounded-lg transition-colors"
                >
                  Reset
                </button>
              </div>

              {/* Info */}
              <div className="mt-6 p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                <p className="text-xs text-slate-400">
                  <strong className="text-slate-300">Note:</strong> Changes will reinitialize the engine and clear all active sessions.
                </p>
              </div>
            </>
          )}

        </div>
      </div>
    </>
  );
};
