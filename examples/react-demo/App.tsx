import React, { useState, useRef, useEffect, useCallback } from 'react';
import { AVAILABLE_TOOLS, SUGGESTION_DEBOUNCE_MS } from './constants';
import { Tool, Message, ConnectionStatus, SuggestionMode } from './types';
import {
  getToolSuggestions,
  initializeSuggestionService,
  onSuggestionsReceived,
  onConnectionStatusChange,
  submitText,
  resetSession,
  getSuggestionMode,
  getConnectionStatus
} from './services/suggestionService';
import { generateChatResponse } from './services/geminiService';
import { SuggestionItem } from './components/SuggestionItem';
import { ChatBubble } from './components/ChatBubble';
import { SettingsSidebar } from './components/SettingsSidebar';

const App: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState<Tool[]>([]);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'model',
      text: 'Hello! I am the Suggester demo. Start typing to see real-time tool suggestions, or ask me a complex question.',
      timestamp: Date.now()
    }
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [suggestionMode, setSuggestionMode] = useState<SuggestionMode>('websocket');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const suggestionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const previousInputRef = useRef<string>('');

  // Initialize WebSocket connection on mount
  useEffect(() => {
    const initialize = async () => {
      await initializeSuggestionService();
      setSuggestionMode(getSuggestionMode());
      setConnectionStatus(getConnectionStatus());
    };

    initialize();

    // Setup callbacks for WebSocket mode
    onSuggestionsReceived((newSuggestions) => {
      setSuggestions(newSuggestions);
    });

    onConnectionStatusChange((status) => {
      setConnectionStatus(status);
      if (status === 'connected') {
        setSuggestionMode('websocket');
      }
    });
  }, []);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, suggestions, isProcessing]);

  // Handle input change with debounce for suggestions
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputValue(val);

    if (suggestionTimeoutRef.current) {
      clearTimeout(suggestionTimeoutRef.current);
    }

    suggestionTimeoutRef.current = setTimeout(() => {
      if (suggestionMode === 'websocket') {
        // In WebSocket mode, submit full text (engine handles incremental internally)
        submitText(val);
      } else {
        // Mock mode fallback
        const found = getToolSuggestions(val);
        setSuggestions(found);
      }
      previousInputRef.current = val;
    }, SUGGESTION_DEBOUNCE_MS);
  };

  // Add suggestion to input on click
  const handleSuggestionClick = (tool: Tool) => {
    // Simple append strategy for demo
    setInputValue((prev) => `${prev} use ${tool.name} `);
    // Clear suggestions after selection to acknowledge
    setSuggestions([]); 
  };

  // Handle sending message
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isProcessing) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: inputValue,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setSuggestions([]);
    setIsProcessing(true);

    // Reset WebSocket session when sending message
    if (suggestionMode === 'websocket') {
      resetSession();
    }

    // Add temporary thinking message
    const thinkingMsgId = 'thinking-' + Date.now();
    setMessages(prev => [...prev, {
      id: thinkingMsgId,
      role: 'model',
      text: '',
      timestamp: Date.now(),
      isThinking: true
    }]);

    try {
      // Format history for API
      const history = messages.map(m => ({ role: m.role, text: m.text }));
      const responseText = await generateChatResponse(history, userMsg.text);

      setMessages(prev => prev.map(msg => 
        msg.id === thinkingMsgId 
          ? { ...msg, text: responseText, isThinking: false } 
          : msg
      ));
    } catch (error) {
      setMessages(prev => prev.map(msg => 
        msg.id === thinkingMsgId 
          ? { ...msg, text: "Sorry, something went wrong.", isThinking: false } 
          : msg
      ));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 md:p-8 relative overflow-hidden">
      
      {/* Background Ambience */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[100px] -z-10 pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-emerald-600/5 rounded-full blur-[120px] -z-10 pointer-events-none" />

      <div className="w-full max-w-3xl flex flex-col h-[85vh] relative">
        
        {/* Header */}
        <header className="flex items-center justify-between gap-4 mb-6 border-b border-slate-800 pb-4 px-2">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-white">
                 <path fillRule="evenodd" d="M9.315 7.584C12.195 3.883 16.695 1.5 21.75 1.5a.75.75 0 01.75.75c0 5.056-2.383 9.555-6.084 12.436A6.75 6.75 0 019.75 22.5a.75.75 0 01-.75-.75v-4.131A15.838 15.838 0 016.382 15H2.25a.75.75 0 01-.75-.75 6.75 6.75 0 017.815-6.666zM15 6.75a2.25 2.25 0 100 4.5 2.25 2.25 0 000-4.5z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
               <h1 className="text-xl font-bold text-white tracking-tight">Suggester</h1>
               <p className="text-xs text-slate-400">Real-time Intent & Tool Detection Demo</p>
            </div>
          </div>

          {/* Settings Button */}
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors group"
            title="Engine Settings"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-slate-400 group-hover:text-indigo-400 transition-colors">
              <path fillRule="evenodd" d="M11.078 2.25c-.917 0-1.699.663-1.85 1.567L9.05 4.889c-.02.12-.115.26-.297.348a7.493 7.493 0 00-.986.57c-.166.115-.334.126-.45.083L6.3 5.508a1.875 1.875 0 00-2.282.819l-.922 1.597a1.875 1.875 0 00.432 2.385l.84.692c.095.078.17.229.154.43a7.598 7.598 0 000 1.139c.015.2-.059.352-.153.43l-.841.692a1.875 1.875 0 00-.432 2.385l.922 1.597a1.875 1.875 0 002.282.818l1.019-.382c.115-.043.283-.031.45.082.312.214.641.405.985.57.182.088.277.228.297.35l.178 1.071c.151.904.933 1.567 1.85 1.567h1.844c.916 0 1.699-.663 1.85-1.567l.178-1.072c.02-.12.114-.26.297-.349.344-.165.673-.356.985-.57.167-.114.335-.125.45-.082l1.02.382a1.875 1.875 0 002.28-.819l.923-1.597a1.875 1.875 0 00-.432-2.385l-.84-.692c-.095-.078-.17-.229-.154-.43a7.614 7.614 0 000-1.139c-.016-.2.059-.352.153-.43l.84-.692c.708-.582.891-1.59.433-2.385l-.922-1.597a1.875 1.875 0 00-2.282-.818l-1.02.382c-.114.043-.282.031-.449-.083a7.49 7.49 0 00-.985-.57c-.183-.087-.277-.227-.297-.348l-.179-1.072a1.875 1.875 0 00-1.85-1.567h-1.843zM12 15.75a3.75 3.75 0 100-7.5 3.75 3.75 0 000 7.5z" clipRule="evenodd" />
            </svg>
          </button>
        </header>

        {/* Chat Area */}
        <main className="flex-grow overflow-y-auto px-2 pb-32 relative space-y-4">
          {messages.map(msg => (
            <ChatBubble key={msg.id} message={msg} />
          ))}
          <div ref={chatEndRef} />
        </main>

        {/* Input & Suggestions Container (Sticky Bottom) */}
        <div className="absolute bottom-0 left-0 right-0 px-2 pb-2 bg-gradient-to-t from-slate-950 via-slate-950 to-transparent pt-10">
          <div className="relative max-w-3xl mx-auto w-full">
            
            {/* Suggestions Panel - Floats above input */}
            {suggestions.length > 0 && (
              <div className="mb-3 animate-slide-up">
                <div className="flex items-center justify-between px-2 mb-2">
                   <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Suggested Tools</span>
                   <span className="text-[10px] text-slate-600">{suggestions.length} matches</span>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {suggestions.map(tool => (
                    <SuggestionItem key={tool.id} tool={tool} onClick={handleSuggestionClick} />
                  ))}
                </div>
              </div>
            )}

            {/* Input Field */}
            <div className="relative group">
               <input
                 type="text"
                 value={inputValue}
                 onChange={handleInputChange}
                 onKeyDown={handleKeyDown}
                 placeholder="Try 'export csv' or 'send email'..."
                 className="w-full bg-slate-900/80 border border-slate-700/50 rounded-2xl py-4 pl-5 pr-14 text-slate-200 placeholder-slate-500 
                            focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-transparent focus:bg-slate-900
                            shadow-xl backdrop-blur-sm transition-all duration-200"
                 autoFocus
               />
               
               <button 
                 onClick={handleSendMessage}
                 disabled={!inputValue.trim() || isProcessing}
                 className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-indigo-600 rounded-xl text-white 
                            hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 transition-colors shadow-lg shadow-indigo-500/20"
               >
                 {isProcessing ? (
                   <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                     <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                     <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                   </svg>
                 ) : (
                   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                     <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                   </svg>
                 )}
               </button>
            </div>
            
            <div className="mt-2 flex justify-center gap-4 opacity-50">
               <div className="flex items-center gap-1">
                  <div className={`w-1 h-1 rounded-full ${
                    connectionStatus === 'connected' ? 'bg-emerald-500' :
                    connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                    connectionStatus === 'error' ? 'bg-red-500' :
                    'bg-gray-500'
                  }`}></div>
                  <span className="text-[10px] text-slate-500">
                    Suggester {suggestionMode === 'websocket' ? 'Python Engine' : 'Mock'} ({connectionStatus})
                  </span>
               </div>
               <div className="flex items-center gap-1">
                  <div className="w-1 h-1 rounded-full bg-indigo-500"></div>
                  <span className="text-[10px] text-slate-500">Gemini 3.0 Pro (Thinking)</span>
               </div>
            </div>

          </div>
        </div>

      </div>

      {/* Settings Sidebar */}
      <SettingsSidebar
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
};

export default App;