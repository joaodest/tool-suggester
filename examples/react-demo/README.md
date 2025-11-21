# Suggester React Demo

**Live demonstration of Suggester's WebSocket-based real-time tool suggestion engine**

This demo application showcases how to integrate Suggester with a React frontend using WebSocket for real-time, low-latency tool suggestions as users type.

---

## What This Demo Shows

- **Real-time suggestions**: Tool recommendations appear as you type (sub-10ms latency)
- **WebSocket integration**: Persistent connection for instant updates
- **Session management**: Per-user state tracking
- **Multi-intent detection**: Suggest multiple tools for complex queries
- **Gemini AI Chat**: Full conversational AI interface powered by Google Gemini
- **Auto-reconnection**: Graceful fallback and reconnection handling

---

## Quick Start

### Prerequisites

- Python 3.9+ (for backend)
- Node.js 18+ (for frontend)
- Gemini API key (for chat functionality)

### Option 1: One-Command Startup (Recommended)

From the repository root:

```bash
python start_demo.py
```

This automatically starts both backend and frontend servers.

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
# From repository root
python -m src.suggester.adapters.react_gateway
```

**Terminal 2 - Frontend:**
```bash
# From repository root
cd examples/react-demo/
npm install
npm run dev
```

### Access the Demo

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **WebSocket**: ws://localhost:8000/ws/suggest
- **Health Check**: http://localhost:8000/health

---

## Architecture

```
┌──────────────────────────────────────────────┐
│           React Frontend (Vite)              │
│                                              │
│  ┌────────────┐      ┌──────────────────┐  │
│  │  App.tsx   │◄─────┤ websocketService │  │
│  │            │      │       .ts        │  │
│  │  - Chat UI │      │                  │  │
│  │  - Input   │      │  - Auto-reconnect│  │
│  │  - Suggestions    │  - Ping/pong    │  │
│  └────────────┘      └─────────┬────────┘  │
│                                 │            │
└─────────────────────────────────┼────────────┘
                                  │
                            WebSocket
                            (port 8000)
                                  │
┌─────────────────────────────────┼────────────┐
│      Python Backend (FastAPI)   │            │
│                                 │            │
│  ┌──────────────────────────────▼─────────┐ │
│  │      react_gateway.py                  │ │
│  │  - WebSocket: /ws/suggest              │ │
│  │  - REST fallback: /api/suggest         │ │
│  │  - Health: /health                     │ │
│  │  - Config: /api/config                 │ │
│  └────────────────┬───────────────────────┘ │
│                   │                          │
│  ┌────────────────▼───────────────────────┐ │
│  │      SuggestionEngine                  │ │
│  │  - TRIE + Inverted Index              │ │
│  │  - Multi-intent detection              │ │
│  │  - Session management                  │ │
│  │  - 16 sample tools (8 tools + 8 MCPs) │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## WebSocket Protocol

### Client → Server Messages

**1. Submit (complete text)**
```json
{
  "type": "submit",
  "session_id": "user-session-123",
  "text": "export data to csv"
}
```

**2. Feed (incremental delta)**
```json
{
  "type": "feed",
  "session_id": "user-session-123",
  "delta": " and"
}
```

**3. Reset (clear session)**
```json
{
  "type": "reset",
  "session_id": "user-session-123"
}
```

**4. Ping (heartbeat)**
```json
{
  "type": "ping",
  "session_id": "user-session-123",
  "timestamp": 1705089600000
}
```

### Server → Client Messages

**1. Suggestions**
```json
{
  "type": "suggestions",
  "session_id": "user-session-123",
  "suggestions": [
    {
      "id": "export_csv",
      "kind": "tool",
      "score": 8.5,
      "label": "export_csv",
      "reason": "export: keywords; csv: keywords",
      "arguments_template": {},
      "metadata": {"tags": ["data", "io", "export"]}
    }
  ]
}
```

**2. Pong (heartbeat response)**
```json
{
  "type": "pong",
  "timestamp": 1705089600000
}
```

**3. Error**
```json
{
  "type": "error",
  "error": "Error description"
}
```

---

## Key Components

### Frontend (React + TypeScript)

**`services/websocketService.ts`**
- Manages WebSocket connection lifecycle
- Auto-reconnection with exponential backoff (max 5 attempts)
- Heartbeat ping/pong every 30s
- Singleton pattern for connection sharing

**`services/suggestionService.ts`**
- Abstraction layer over WebSocket
- Fallback to mock mode if WebSocket unavailable
- Callbacks for suggestions and connection status

**`App.tsx`**
- Main chat interface
- Real-time suggestion display
- Gemini AI integration for chat responses
- Visual connection status indicator

### Backend (Python + FastAPI)

**`src/suggester/adapters/react_gateway.py`**
- FastAPI application with WebSocket support
- CORS enabled for local development
- Loads 16 sample tools from demo catalog
- Session-based suggestion engine

**Sample Tools**
- 8 traditional tools (export_csv, send_email, db_query, etc.)
- 8 MCP-style tools (filesystem.read, api.call, etc.)

---

## Try These Queries

**Single-intent:**
- "export data to csv"
- "send an email notification"
- "query the database"
- "translate text to spanish"

**Multi-intent (Beta):**
- "export data, send email, and generate report"
- "search customers and send notifications"
- "query database then export to csv"

---

## Troubleshooting

### "WebSocket unavailable, using mock mode"

**Cause**: Backend is not running

**Solution**:
```bash
# From repository root
python -m src.suggester.adapters.react_gateway
```

### Port 8000 Already in Use

**Windows:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -i :8000
kill -9 <PID>
```

### Suggestions Not Appearing

**Check:**
1. Connection status indicator in UI (should show "connected")
2. Backend logs for errors
3. Browser console Network tab for WebSocket activity
4. Query has at least 2 characters

### Frontend Won't Start

**Solution:**
```bash
cd examples/react-demo/
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## Performance

| Metric | Target | Actual |
|--------|--------|--------|
| Latency (p95) | <10ms | ~5ms |
| WebSocket Reconnect | Auto | 5 attempts |
| Debounce | 300ms | 300ms |
| Sample Tools | - | 16 |

---

## Integration with Your App

To integrate Suggester WebSocket into your own React app:

1. **Copy service files:**
   ```bash
   cp examples/react-demo/services/*.ts your-app/src/services/
   cp examples/react-demo/types.ts your-app/src/
   ```

2. **Initialize in your component:**
   ```typescript
   import { connectToSuggestions } from './services/suggestionService';

   useEffect(() => {
     connectToSuggestions({
       onSuggestions: (suggestions) => {
         console.log('New suggestions:', suggestions);
       },
       onStatusChange: (status) => {
         console.log('Connection status:', status);
       }
     });
   }, []);
   ```

3. **Send text as user types:**
   ```typescript
   import { submitText, feedText } from './services/suggestionService';

   // On Enter/Submit
   submitText(userInput, sessionId);

   // On keystroke (debounced)
   feedText(delta, sessionId);
   ```

---

## Debug Mode

Enable debug logging in browser console:

```javascript
localStorage.setItem('debug', 'suggester:*');
```

View connection status:
```javascript
import { getConnectionStatus } from './services/suggestionService';
console.log(getConnectionStatus()); // 'connected', 'connecting', 'disconnected', 'error'
```

---

## Learn More

- **Main README**: ../../README.md - Full project documentation
- **Architecture**: ../../docs/planning_tasks.md - Design decisions
- **Backend Gateway**: ../../src/suggester/adapters/react_gateway.py - FastAPI implementation
- **Engine Core**: ../../src/suggester/engine.py - Suggestion algorithm

---

## Notes

- This is a **demonstration application** - not production-ready
- The Gemini API key is stored in `.env.local` (not committed)
- Sample tools are for demo purposes only
- WebSocket connection is **not authenticated** (add auth for production)
- CORS is wide-open for development (restrict for production)

---

**Questions?** See the [main README](../../README.md) or open an issue on [GitHub](https://github.com/joaodest/tool-suggester/issues).
