"""
React Gateway Adapter for Suggester Engine

Lightweight WebSocket/HTTP server for React frontends.
Provides real-time tool suggestions via WebSocket with REST fallback.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    print("Error: FastAPI and uvicorn are required for react_gateway.")
    print("Install with: pip install 'fastapi[standard]' uvicorn")
    sys.exit(1)

# Add parent directory to path to import suggester
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from suggester.engine import SuggestionEngine


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title="Suggester React Gateway",
    description="WebSocket/REST gateway for React frontends",
    version="0.1.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global engine instance (initialized on startup)
engine: SuggestionEngine | None = None
tools_catalog: Dict[str, Any] = {}

# Current engine configuration
current_config: Dict[str, Any] = {
    "top_k": 5,
    "max_intents": 3,
    "locales": ["pt", "en"],
    "min_score": 1.0,
    "combine_strategy": "max",
    "intent_separator_tokens": None  # None means use defaults
}


def load_sample_tools() -> List[Dict[str, Any]]:
    """Load sample tools from demo module."""
    try:
        # Try to import from demo
        demo_path = Path(__file__).parent.parent.parent.parent / "demo"
        sys.path.insert(0, str(demo_path))
        from sample_tools import get_sample_tools
        return get_sample_tools()
    except ImportError:
        logger.warning("Could not import sample_tools, using minimal fallback")
        # Fallback minimal tools
        return [
            {
                "name": "export_csv",
                "description": "Exporta dados para arquivo CSV",
                "keywords": ["exportar", "csv", "salvar", "dados", "planilha"],
                "aliases": ["baixar csv", "gerar csv"],
                "locales": ["pt", "en"],
                "tags": ["data", "io"]
            },
            {
                "name": "send_email",
                "description": "Envia email com anexos",
                "keywords": ["enviar", "email", "mensagem", "correio"],
                "aliases": ["mandar email"],
                "locales": ["pt", "en"],
                "tags": ["communication"]
            }
        ]


def _initialize_engine(config: Dict[str, Any] | None = None) -> None:
    """Initialize or reinitialize the engine with given config."""
    global engine, current_config

    if config:
        current_config.update(config)

    tools = list(tools_catalog.values())

    # Build kwargs from current_config
    kwargs = {
        "top_k": current_config["top_k"],
        "max_intents": current_config["max_intents"],
        "locales": tuple(current_config["locales"]),
        "min_score": current_config["min_score"],
        "combine_strategy": current_config["combine_strategy"],
    }

    # Add intent_separator_tokens only if provided
    if current_config["intent_separator_tokens"] is not None:
        kwargs["intent_separator_tokens"] = current_config["intent_separator_tokens"]

    logger.info(f"Initializing SuggestionEngine with config: {kwargs}")
    engine = SuggestionEngine(tools, **kwargs)


@app.on_event("startup")
async def startup_event():
    """Initialize engine on startup."""
    global tools_catalog

    logger.info("Loading tools catalog...")
    tools = load_sample_tools()
    tools_catalog = {tool["name"]: tool for tool in tools}

    logger.info(f"Initializing SuggestionEngine with {len(tools)} tools...")
    _initialize_engine()

    logger.info("✓ Suggester Gateway started successfully")
    logger.info(f"  - Tools loaded: {len(tools)}")
    logger.info(f"  - WebSocket endpoint: ws://localhost:8000/ws/suggest")
    logger.info(f"  - REST endpoint: http://localhost:8000/api/suggest")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "Suggester React Gateway",
        "version": "0.1.0",
        "status": "running",
        "tools_count": len(tools_catalog),
        "endpoints": {
            "websocket": "/ws/suggest",
            "rest": "/api/suggest",
            "health": "/health",
            "tools": "/api/tools"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "engine_initialized": engine is not None,
        "tools_loaded": len(tools_catalog)
    }


@app.get("/api/tools")
async def get_tools():
    """Get all available tools."""
    return {
        "tools": list(tools_catalog.values()),
        "count": len(tools_catalog)
    }


@app.get("/api/config")
async def get_config():
    """Get current engine configuration."""
    return {
        "config": current_config,
        "status": "ok"
    }


@app.post("/api/config")
async def update_config(payload: Dict[str, Any]):
    """Update engine configuration and reinitialize."""
    try:
        # Validate config parameters
        new_config = {}

        if "top_k" in payload:
            top_k = int(payload["top_k"])
            if top_k < 1 or top_k > 20:
                return {"error": "top_k must be between 1 and 20"}, 400
            new_config["top_k"] = top_k

        if "max_intents" in payload:
            max_intents = int(payload["max_intents"])
            if max_intents < 1 or max_intents > 10:
                return {"error": "max_intents must be between 1 and 10"}, 400
            new_config["max_intents"] = max_intents

        if "min_score" in payload:
            min_score = float(payload["min_score"])
            if min_score < 0.0:
                return {"error": "min_score must be >= 0.0"}, 400
            new_config["min_score"] = min_score

        if "combine_strategy" in payload:
            strategy = str(payload["combine_strategy"]).lower()
            if strategy not in ["max", "sum"]:
                return {"error": "combine_strategy must be 'max' or 'sum'"}, 400
            new_config["combine_strategy"] = strategy

        if "intent_separator_tokens" in payload:
            tokens = payload["intent_separator_tokens"]
            if tokens is None:
                new_config["intent_separator_tokens"] = None
            elif isinstance(tokens, list):
                new_config["intent_separator_tokens"] = [str(t).strip() for t in tokens if str(t).strip()]
            elif isinstance(tokens, str):
                # Parse comma-separated string
                new_config["intent_separator_tokens"] = [t.strip() for t in tokens.split(",") if t.strip()]
            else:
                return {"error": "intent_separator_tokens must be a list or comma-separated string"}, 400

        if "locales" in payload:
            locales = payload["locales"]
            if isinstance(locales, list):
                new_config["locales"] = [str(loc).strip() for loc in locales if str(loc).strip()]
            elif isinstance(locales, str):
                new_config["locales"] = [loc.strip() for loc in locales.split(",") if loc.strip()]

        # Reinitialize engine with new config
        _initialize_engine(new_config)

        logger.info(f"Configuration updated: {new_config}")

        return {
            "status": "ok",
            "message": "Engine reinitialized with new configuration",
            "config": current_config
        }

    except ValueError as e:
        logger.error(f"Invalid config value: {e}")
        return {"error": f"Invalid value: {str(e)}"}, 400
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return {"error": str(e)}, 500


@app.post("/api/suggest")
async def suggest_rest(payload: Dict[str, Any]):
    """REST endpoint for suggestions (fallback)."""
    if engine is None:
        return {"error": "Engine not initialized"}, 500

    text = payload.get("text", "")
    session_id = payload.get("session_id", "default")
    action = payload.get("action", "submit")  # submit, feed, reset

    try:
        if action == "reset":
            engine.reset(session_id)
            return {"status": "reset", "session_id": session_id}

        elif action == "feed":
            delta = payload.get("delta", "")
            suggestions = engine.feed(delta, session_id=session_id)

        else:  # submit
            suggestions = engine.submit(text, session_id=session_id)

        return {
            "suggestions": suggestions,
            "session_id": session_id,
            "text": text
        }

    except Exception as e:
        logger.error(f"Error processing suggestion: {e}")
        return {"error": str(e)}, 500


@app.websocket("/ws/suggest")
async def websocket_suggest(websocket: WebSocket):
    """WebSocket endpoint for real-time suggestions."""
    await websocket.accept()
    session_id = None

    logger.info("WebSocket client connected")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")
            session_id = message.get("session_id", "default")

            if msg_type == "feed":
                # Incremental text delta
                delta = message.get("delta", "")
                suggestions = engine.feed(delta, session_id=session_id)

                await websocket.send_json({
                    "type": "suggestions",
                    "suggestions": suggestions,
                    "session_id": session_id
                })

            elif msg_type == "submit":
                # Full text submission
                text = message.get("text", "")
                suggestions = engine.submit(text, session_id=session_id)

                await websocket.send_json({
                    "type": "suggestions",
                    "suggestions": suggestions,
                    "session_id": session_id
                })

            elif msg_type == "reset":
                # Reset session
                engine.reset(session_id)

                await websocket.send_json({
                    "type": "reset",
                    "session_id": session_id,
                    "status": "ok"
                })

            elif msg_type == "ping":
                # Health check
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": message.get("timestamp")
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected (session: {session_id})")
        if session_id and engine:
            engine.reset(session_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the gateway server."""
    logger.info(f"Starting Suggester Gateway on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
