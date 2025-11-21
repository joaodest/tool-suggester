# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Suggester** is a lightweight, plug-and-play tool suggestion engine that provides real-time tool/MCP suggestions as users type in LLM-based UIs (OpenWebUI, Streamlit, Chainlit, React, etc.). It operates locally by default with optional LLM re-ranking.

Key characteristics:
- **Lexical matching** using TRIE-based incremental indexing
- **Framework-agnostic** - works with any LLM framework (LangChain, LangGraph, CrewAI, etc.)
- **Low latency** target: <10ms per text delta (p95)
- **Session-based state** management for streaming text input

## Development Commands

### Installation
```bash
# Install in editable mode for development
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_engine.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src/suggester
```

### Code Quality
```bash
# Format code with black
black src/ tests/ demo/

# Lint with ruff
ruff check src/ tests/ demo/

# Type checking with mypy
mypy src/
```

### Running Demos
```bash
# Streamlit chat demo (requires streamlit and st_keyup)
streamlit run demo/chat_app.py

# Test sample tools catalog
python demo/sample_tools.py
```

## Architecture

### Core Components

1. **SuggestionEngine** (`src/suggester/engine.py`)
   - Main API entry point
   - Manages per-session state (text buffer)
   - Coordinates tokenization, TRIE lookup, and ranking
   - Two key methods:
     - `feed(text_delta, session_id)`: Incremental text streaming
     - `submit(text, session_id)`: Full text submission

2. **TRIE Index** (`src/suggester/trie.py`)
   - Prefix-based term matching
   - `insert(term)`: Build index from tool keywords
   - `prefix_terms(prefix, limit)`: Fast prefix search

3. **Tokenization** (`src/suggester/tokenizer.py`)
   - `normalize(text)`: Case-folding, accent removal
   - `tokens(text)`: Split text into searchable terms
   - Locale-aware normalization (pt, en)

4. **Ranking** (`src/suggester/ranking.py`)
   - `rank_tools(tool_term_counts, term_lengths)`: Score calculation
   - Considers term frequency, term length/rarity
   - Returns sorted tool scores

### Data Flow

```
User types → Engine.feed(delta) → Tokenizer → TRIE lookup → Ranking → Top-K Suggestions
                    ↓
            Session buffer updated
```

### Key Data Structures

**ToolSpec** (TypedDict in `schemas.py`):
- Required: `name`, `description`
- Optional: `keywords`, `aliases`, `tags`, `args_schema`, `locales`

**Suggestion** (TypedDict in `schemas.py`):
- `id`: Tool identifier
- `kind`: "tool" or "mcp"
- `score`: Ranking score
- `label`: Display name
- `reason`: Match explanation
- `arguments_template`: Pre-filled args (optional)

### Session Management

The engine maintains a `_sessions` dict mapping `session_id` to `_Session(buffer)`:
- **Incremental updates**: `feed()` appends to buffer and uses delta for efficient matching
- **Full reset**: `submit()` replaces entire buffer
- **Cleanup**: `reset(session_id)` clears session state

## Streamlit Demo Architecture

The `demo/chat_app.py` uses **Streamlit fragments** for optimal performance:

- **`@st.fragment` decorator**: Isolates the search/suggestions UI to prevent full page reruns
- **`st_keyup` component**: Real-time keystroke detection with 300ms debounce
- **Sample tools**: `demo/sample_tools.py` provides 16 example tools (8 traditional + 8 MCP-style)

Fragment isolation ensures:
- Text input maintains focus during updates
- Sidebar doesn't flicker
- Only suggestion area re-renders

## Important Implementation Details

### Tool Catalog Construction

Tools are indexed at initialization time:
1. Extract terms from `name`, `description`, `keywords`, `aliases`
2. Normalize all terms via `tokenizer.normalize()`
3. Insert each term into TRIE with back-reference to tool name
4. Build `_term_to_tools` mapping for fast lookup

### Matching Strategy

1. **Split input into tokens**: Last token is treated as prefix, others as complete terms
2. **Complete terms**: Exact match in `_term_to_tools`
3. **Prefix matching**: TRIE search for partial last token (max 64 results)
4. **Tool scoring**: Count matched terms per tool, weight by term length
5. **Top-K selection**: Return highest scoring tools (default: 5)

### MCP vs Tool Detection

Tools with names starting with `db.`, `api.`, `mcp.`, or `filesystem.` are classified as MCPs in the demo UI. This is a convention, not enforced by the core engine.

## Common Patterns

### Adding New Tools Dynamically

```python
engine = SuggestionEngine(initial_tools)

# Add more tools later
new_tools = [{"name": "new_tool", "description": "...", "keywords": [...]}]
engine.add_tools(new_tools)

# Remove a tool
engine.remove_tool("tool_name")  # Note: rebuilds entire index
```

### Session-Based Usage

```python
# User starts typing
suggestions = engine.feed("expor", session_id="user123")

# User continues
suggestions = engine.feed("t", session_id="user123")  # Now buffer = "export"

# User deletes text - reset and resubmit
engine.reset("user123")
suggestions = engine.submit("exp", session_id="user123")
```

### Custom Streamlit Integration

When building custom Streamlit UIs with this engine:
1. Use `@st.fragment` to wrap search/suggestions UI
2. Use `st_keyup` for real-time updates (not `st.text_input`)
3. Set appropriate `debounce` (300-500ms recommended)
4. Check `if new_text != st.session_state.previous_text` before updating

## Testing Strategy

- **Unit tests**: Core algorithms (TRIE, tokenizer, ranking)
- **Integration tests**: Engine with real tool catalogs
- **Strict tests**: `test_engine_strict.py` validates exact behavior

Test files follow `test_<module>.py` naming convention.

## Performance Considerations

- **TRIE prefix search** is capped at 64 results to avoid slowdowns
- **Debouncing** (300ms default) prevents excessive recomputation during fast typing
- **Session state** is lightweight (just text buffer)
- **Index rebuilding** (on `remove_tool`) is expensive - batch removals when possible

## Future Extensions (from docs/planning_tasks.md)

- LLM-based re-ranking (opt-in)
- Aho-Corasick for multi-pattern matching
- WebSocket gateway for React/web clients
- MCP server introspection adapter
- LangChain/LangGraph/CrewAI integrations
- Persistent index caching (pickle)

## References

- **Architecture docs**: `docs/planning_tasks.md` (comprehensive design document)
- **Matching v2**: `docs/matching_v2_plan.md` (inverted index optimization plan)
- **Sample catalog**: `demo/sample_tools.py` (16 example tools with full schemas)