from __future__ import annotations

from typing import Any, Dict, List, Literal, TypedDict


class ToolSpec(TypedDict, total=False):
    name: str
    description: str
    args_schema: Dict[str, Any]
    keywords: List[str]
    aliases: List[str]
    locales: List[str]
    tags: List[str]


class Suggestion(TypedDict, total=False):
    id: str
    kind: Literal["tool", "mcp"]
    score: float
    label: str
    reason: str
    arguments_template: Dict[str, Any]
    metadata: Dict[str, Any]

# Fields used in inverted index
Field = Literal["name", "keywords", "aliases", "description"]
