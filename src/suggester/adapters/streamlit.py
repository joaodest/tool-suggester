from __future__ import annotations

from typing import Any, Dict, List, Tuple


def suggest_box(label: str, *, tools: List[Dict[str, Any]], key: str = "suggest_box") -> Tuple[dict, List[dict]]:
    """Conceptual component for Streamlit.

    Returns (selected, suggestions). Minimal implementation to avoid depending
    on Streamlit in the package core. In a real app, integrate with st.text_input
    and render suggestions as the user types.
    """
    try:
        import streamlit as st  # type: ignore
    except Exception as exc:  # pragma: no cover - fallback only
        raise ImportError("streamlit not installed") from exc

    from ..engine import SuggestionEngine

    engine = SuggestionEngine(tools)
    text = st.text_input(label, key=key)
    suggestions = engine.submit(text, session_id=key)
    selected = suggestions[0] if suggestions else None
    return selected, suggestions

