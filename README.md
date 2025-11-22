# Suggester

<div align="center">

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Tests](https://img.shields.io/badge/tests-pytest-green)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Lightweight, plug-and-play tool suggestion engine for LLM-based UIs**

Real-time tool/MCP suggestions as users type in OpenWebUI, Streamlit, Chainlit, React, and more.

[Quick Start](#quick-start) • [Features](#features) • [Architecture](#architecture) • [Integration](#integration-guides) • [API](#api-reference) • [Examples](#examples)

</div>

---

## Overview

**Suggester** provides real-time, intelligent tool suggestions as users type in LLM-based interfaces. It operates locally by default with sub-10ms latency, using lexical matching and optional LLM re-ranking.

### Key Features

- **Real-time suggestions** via TRIE-based incremental indexing with TF-IDF scoring
- **Free-text matching** with anchored windows and lightweight stopwords (PT/EN)
- **Multi-intent support** - detect and suggest multiple actions in a single query (e.g., "export data, send email, and generate report")
- **Framework-agnostic** - works with any LLM framework (LangChain, LangGraph, CrewAI, etc.)
- **Low latency** - <10ms p95 per text delta
- **Session-based state** - streaming text input with automatic buffer management
- **Plug-and-play** - simple Python API with optional connectors (WebSocket, Streamlit, React)

### Use Cases

- **OpenWebUI**: Suggest tools as users type prompts
- **Streamlit apps**: Real-time tool recommendations in chat interfaces
- **React frontends**: WebSocket-based live suggestions
- **CLI tools**: Autocomplete-style tool discovery
- **Agent frameworks**: Dynamic tool selection for autonomous agents

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/joaodest/tool-suggester.git
cd tool-suggester

# Install in editable mode
pip install -e .

# Install with dev dependencies (for contributors)
pip install -e ".[dev]"
```

### Basic Usage

```python
from suggester.engine import SuggestionEngine

# Define your tools
tools = [
    {
        "name": "export_csv",
        "description": "Export data to CSV format",
        "keywords": ["export", "csv", "file", "download"]
    },
    {
        "name": "send_email",
        "description": "Send email notifications",
        "keywords": ["email", "send", "notify", "message"]
    },
    {
        "name": "db_query",
        "description": "Query database records",
        "keywords": ["database", "query", "search", "find", "select"]
    },
]

# Initialize the engine
engine = SuggestionEngine(tools)

# Get suggestions as user types
suggestions = engine.submit(
    "I need to export my data to a csv file",
    session_id="user-session-123"
)

print(suggestions)
# [{'id': 'export_csv', 'kind': 'tool', 'score': 8.5, 'label': 'export_csv', ...}]
```

### Multi-Intent Detection (Beta)

```python
# Enable multi-intent support
multi_engine = SuggestionEngine(
    tools,
    max_intents=3,
    intent_separator_tokens=["and", "then", "also", "e", "depois"],
    combine_strategy="sum"
)

# Detect multiple actions in one query
suggestions = multi_engine.submit(
    "Query the database, export results to CSV, and send an email notification",
    session_id="multi-intent-session"
)

# Returns suggestions for all three tools: db_query, export_csv, send_email
print(len(suggestions))  # 3 tools suggested
```

### Run the Demo

**Option 1: One-command startup**

```bash
python start_demo.py
```

This automatically starts:
- Python backend (port 8000)
- React frontend (port 5173)

Access at: http://localhost:5173

**Option 2: Manual startup**

Terminal 1 (Backend):
```bash
python -m src.suggester.adapters.react_gateway
```

Terminal 2 (Frontend):
```bash
cd examples/react-demo/
npm install
npm run dev
```

---

## Features

### Core Engine

- **TRIE-based indexing**: Fast prefix matching for incremental text input
- **Inverted index with TF-IDF**: Keyword-based scoring for relevance ranking
- **Intent window detection**: Anchored window parsing for multi-intent queries
- **Stopword filtering**: Lightweight PT/EN stopwords to improve matching accuracy
- **Session management**: Stateful buffer per session for streaming text deltas
- **Configurable ranking**: Adjust `top_k`, `combine_strategy`, and separator tokens

### API Modes

- **`submit(text, session_id)`**: Process complete text (e.g., on Enter/submit)
- **`feed(delta, session_id)`**: Incremental text streaming (e.g., keystroke-by-keystroke)
- **`reset(session_id)`**: Clear session buffer

### Adapters

- **WebSocket Gateway**: Real-time suggestions for web frontends (FastAPI + uvicorn)
- **Streamlit**: Fragment-based UI with `st_keyup` for debounced input
- **REST API fallback**: HTTP endpoint for non-WebSocket clients

---

## Architecture

### Design Principles

1. **Local-first**: No external API calls required (optional LLM re-ranking)
2. **Latency-optimized**: TRIE + inverted index for sub-10ms lookups
3. **Stateful sessions**: Maintain per-user text buffers for streaming
4. **Framework-agnostic**: Core engine has no dependencies on LLM frameworks

### Component Overview

![Overview]<img width="3210" height="3625" alt="tool_architecture" src="https://github.com/user-attachments/assets/48140de5-3383-4456-bce7-f5e47da7e296" />

### Data Flow

1. **User types**: "export data to csv"
2. **Engine.submit()**: Tokenize → "export", "data", "csv"
3. **TRIE lookup**: Find all tools matching these terms
4. **Inverted index**: Score tools by term frequency and TF-IDF
5. **Ranking**: Sort by score, return top-K
6. **Result**: `[{id: "export_csv", score: 8.5, ...}]`

### Key Algorithms

- **TRIE prefix search**: O(m) where m = query length
- **Inverted index lookup**: O(k) where k = matched tools
- **TF-IDF scoring**: Balances term frequency with rarity
- **Anchored window parsing**: Segments multi-intent queries by separator tokens

---

## Integration Guides

### React (WebSocket)

The included React demo (`examples/react-demo/`) demonstrates WebSocket integration:

**Backend** (`src/suggester/adapters/react_gateway.py`):
- FastAPI + uvicorn server
- WebSocket endpoint: `ws://localhost:8000/ws/suggest`
- REST fallback: `POST /api/suggest`

**Frontend** (`examples/react-demo/services/websocketService.ts`):
- Auto-reconnection (max 5 attempts)
- Ping/pong heartbeat
- TypeScript types for suggestions

**Protocol** (WebSocket messages):

Client → Server:
```json
{"type": "submit", "session_id": "user-123", "text": "export data"}
{"type": "feed", "session_id": "user-123", "delta": " to"}
{"type": "reset", "session_id": "user-123"}
```

Server → Client:
```json
{
  "type": "suggestions",
  "session_id": "user-123",
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

See [`examples/react-demo/README.md`](examples/react-demo/README.md) for full details.

### Streamlit

```python
import streamlit as st
from st_keyup import st_keyup
from suggester.engine import SuggestionEngine

# Initialize engine (cached)
@st.cache_resource
def get_engine():
    return SuggestionEngine(load_tools())

engine = get_engine()

# Use st_keyup for real-time input
user_input = st_keyup("Type your query:", debounce=300, key="user_input")

if user_input:
    suggestions = engine.feed(user_input, session_id=st.session_state.session_id)

    # Display suggestions in sidebar
    with st.sidebar:
        st.write("**Suggested Tools:**")
        for sug in suggestions:
            st.write(f"- {sug['label']} (score: {sug['score']:.1f})")
```

**Tips**:
- Use `@st.fragment` to isolate suggestion UI and prevent full reruns
- Set `debounce=300` to avoid excessive recomputation
- See `CLAUDE.md` for full Streamlit integration details

### LangChain / LangGraph

```python
from langchain.tools import Tool
from suggester.engine import SuggestionEngine

# Convert LangChain tools to Suggester format
langchain_tools = [...]  # Your LangChain tools
suggester_tools = [
    {
        "name": tool.name,
        "description": tool.description,
        "keywords": tool.name.lower().split("_") + tool.description.lower().split()[:5],
    }
    for tool in langchain_tools
]

engine = SuggestionEngine(suggester_tools)

# Use in agent loop
user_query = "I need to search the web and send an email"
suggested_tool_ids = [s["id"] for s in engine.submit(user_query, session_id="agent")]

# Filter LangChain tools by suggestion
relevant_tools = [t for t in langchain_tools if t.name in suggested_tool_ids]
```

### CrewAI / Autogen

Similar to LangChain - convert your framework's tool definitions to Suggester's `ToolSpec` format:

```python
from suggester.schemas import ToolSpec

tools: list[ToolSpec] = [
    {
        "name": "web_search",
        "description": "Search the web for information",
        "keywords": ["search", "web", "google", "query", "find"],
        "aliases": ["google", "bing"],
        "tags": ["web", "search"],
        "locales": ["en", "pt"],
    }
]
```

---

## API Reference

### `SuggestionEngine`

Main entry point for the suggestion engine.

```python
class SuggestionEngine:
    def __init__(
        self,
        tools: list[ToolSpec],
        top_k: int = 5,
        max_intents: int = 1,
        intent_separator_tokens: str | list[str] = "",
        combine_strategy: Literal["sum", "max"] = "max",
    ):
        """
        Args:
            tools: List of tool specifications (name, description, keywords, etc.)
            top_k: Maximum number of suggestions to return per intent
            max_intents: Maximum number of intents to detect (1 = single intent)
            intent_separator_tokens: Tokens that separate intents (e.g., "and", "then")
            combine_strategy: How to combine scores across intents ("sum" or "max")
        """
```

#### Methods

**`submit(text: str, session_id: str) -> list[Suggestion]`**

Process complete text submission.

```python
suggestions = engine.submit(
    "export my data to csv",
    session_id="user-123"
)
```

**`feed(delta: str, session_id: str) -> list[Suggestion]`**

Process incremental text delta (for streaming/keystroke input).

```python
# User types: "exp" → "o" → "rt"
suggestions = engine.feed("exp", session_id="user-123")
suggestions = engine.feed("o", session_id="user-123")   # buffer = "expo"
suggestions = engine.feed("rt", session_id="user-123")  # buffer = "export"
```

**`reset(session_id: str) -> None`**

Clear session buffer (e.g., on text deletion or new query).

```python
engine.reset("user-123")
```

**`add_tools(tools: list[ToolSpec]) -> None`**

Dynamically add tools to the index.

```python
new_tools = [{"name": "new_tool", "description": "...", "keywords": [...]}]
engine.add_tools(new_tools)
```

**`remove_tool(tool_name: str) -> None`**

Remove a tool and rebuild index.

```python
engine.remove_tool("deprecated_tool")  # Note: expensive, rebuilds entire index
```

### `ToolSpec` (TypedDict)

Tool specification format.

```python
class ToolSpec(TypedDict, total=False):
    name: str  # Required: unique tool identifier
    description: str  # Required: tool description for matching
    keywords: list[str]  # Optional: explicit keywords for matching
    aliases: list[str]  # Optional: alternative names
    tags: list[str]  # Optional: categorization tags
    args_schema: dict  # Optional: JSON schema for arguments
    locales: list[str]  # Optional: supported locales (e.g., ["en", "pt"])
```

### `Suggestion` (TypedDict)

Suggestion result format.

```python
class Suggestion(TypedDict):
    id: str  # Tool name
    kind: Literal["tool", "mcp"]  # Tool type
    score: float  # Relevance score (higher = better match)
    label: str  # Display name
    reason: str  # Explanation of match (e.g., "export: keywords; csv: keywords")
    arguments_template: dict  # Optional pre-filled arguments
    metadata: dict  # Optional additional metadata (tags, etc.)
```

---

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_engine.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src/suggester

# Disable plugin autoload and ensure local package resolution
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src pytest
```

### Test Structure

- `tests/test_engine.py` - Core engine functionality
- `tests/test_trie.py` - TRIE index tests
- `tests/test_inverted_index.py` - Inverted index tests
- `tests/test_tokenizer.py` - Tokenization tests
- `tests/test_engine_strict.py` - Exact behavior validation
- `tests/test_engine_free_text.py` - Free-text matching tests
- `tests/test_engine_multi_intent.py` - Multi-intent detection tests

---

## Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/

# Type checking with mypy
mypy src/
```

### Project Structure

```
tool-suggester/
├── src/
│   └── suggester/
│       ├── engine.py           # Main SuggestionEngine
│       ├── trie.py             # TRIE index implementation
│       ├── inverted_index.py   # Inverted index + TF-IDF
│       ├── tokenizer.py        # Text normalization & tokenization
│       ├── ranking.py          # Scoring & ranking logic
│       ├── schemas.py          # TypedDict definitions
│       └── adapters/
│           ├── streamlit.py    # Streamlit integration (future)
│           └── react_gateway.py # FastAPI WebSocket gateway
├── tests/
│   ├── test_engine.py
│   ├── test_trie.py
│   └── ...
├── examples/
│   └── react-demo/             # React + WebSocket demo
│       ├── App.tsx
│       ├── services/
│       │   ├── websocketService.ts
│       │   └── suggestionService.ts
│       └── README.md
├── start_demo.py               # One-command demo launcher
├── pyproject.toml              # Package configuration
├── CLAUDE.md                   # Claude Code integration guide
├── CONTRIBUTING.md             # Contribution guidelines
└── README.md                   # This file
```

---

## Examples

### Example 1: Custom Tool Catalog

```python
from suggester.engine import SuggestionEngine

tools = [
    {
        "name": "create_ticket",
        "description": "Create a support ticket in Jira",
        "keywords": ["ticket", "jira", "issue", "bug", "create"],
        "aliases": ["new_ticket", "report_bug"],
        "tags": ["jira", "support"],
    },
    {
        "name": "slack_notify",
        "description": "Send notification to Slack channel",
        "keywords": ["slack", "notify", "message", "send", "alert"],
        "aliases": ["slack_message"],
        "tags": ["slack", "communication"],
    },
]

engine = SuggestionEngine(tools, top_k=3)
suggestions = engine.submit("create a bug report", session_id="dev-123")
print(suggestions[0]["id"])  # "create_ticket"
```

### Example 2: Session Management

```python
engine = SuggestionEngine(tools)

# User 1 session
engine.feed("send", session_id="user1")
engine.feed(" slack", session_id="user1")  # buffer = "send slack"

# User 2 session (independent)
engine.feed("create", session_id="user2")
engine.feed(" ticket", session_id="user2")  # buffer = "create ticket"

# Clear user 1 session
engine.reset("user1")
```

### Example 3: Multi-Language Support

```python
tools = [
    {
        "name": "export_csv",
        "description": "Export data to CSV / Exportar dados para CSV",
        "keywords": ["export", "exportar", "csv", "arquivo", "file"],
        "locales": ["en", "pt"],
    },
]

engine = SuggestionEngine(tools)

# English query
en_suggestions = engine.submit("export to csv", session_id="en-user")

# Portuguese query
pt_suggestions = engine.submit("exportar para csv", session_id="pt-user")

# Both return the same tool
assert en_suggestions[0]["id"] == pt_suggestions[0]["id"]  # "export_csv"
```

See [`examples/react-demo/`](examples/react-demo/) for a complete React + WebSocket integration example.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Before opening a PR:**

1. Run tests: `pytest`
2. Format code: `black src/ tests/`
3. Lint: `ruff check src/ tests/`
4. Type check: `mypy src/`

---

## License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## Links

- **GitHub**: https://github.com/joaodest/tool-suggester
- **Issues**: https://github.com/joaodest/tool-suggester/issues
- **Documentation**: See `docs/` for technical planning documents
- **Claude Code Integration**: See [`CLAUDE.md`](CLAUDE.md)

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## Acknowledgments

- Built for the LLM developer community
- Inspired by IDE autocomplete and tool discovery challenges in agent frameworks
- Optimized for low-latency, local-first operation

---

**Questions?** Open an issue on [GitHub](https://github.com/joaodest/tool-suggester/issues).
