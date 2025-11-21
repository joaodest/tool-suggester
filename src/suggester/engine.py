from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .schemas import Field, Suggestion, ToolSpec
from .tokenizer import normalize, stopwords, tokens, tokens_with_spans
from .trie import Trie
from .inverted_index import InvertedIndex

_DEFAULT_INTENT_SEPARATORS: Tuple[str, ...] = (
    "e",
    "depois",
    "entao",
    "tambem",
    "and",
    "then",
    "after",
    "also",
)


@dataclass
class _Session:
    buffer: str = ""


@dataclass
class _IntentWindow:
    complete_terms: List[str]
    last_prefix: str
    anchor_hits: int


class SuggestionEngine:
    """Lexical suggestion engine with term index and anchored windows."""

    def __init__(
        self,
        tools: Iterable[ToolSpec],
        *,
        locales: Tuple[str, ...] = ("pt", "en"),
        use_llm_reranker: bool = False,
        logger: Any = None,
        telemetry: bool = False,
        top_k: int = 3,
        min_score: float = 1.0,
        require_anchor: bool = True,
        anchor_fields: Tuple[Field, ...] = ("name", "keywords", "aliases"),
        alpha: float = 0.6,
        anchor_alpha: float = 0.5,
        window_radius: int = 3,
        drop_stopwords: bool = True,
        max_intents: int = 1,
        intent_separator_tokens: Sequence[str] | None = None,
        combine_strategy: str = "max",
        multi_intent_bonus: float = 0.0,
    ) -> None:
        self._logger = logger
        self._locales = tuple(locales)
        self._use_llm = use_llm_reranker
        self._telemetry = telemetry
        self._top_k = top_k
        self._min_score = float(min_score)
        self._require_anchor = bool(require_anchor)
        self._anchor_fields = tuple(anchor_fields)
        self._alpha = float(alpha)
        self._anchor_alpha = float(anchor_alpha)
        self._window_radius = max(0, int(window_radius))
        self._drop_stopwords = bool(drop_stopwords)
        self._max_intents = max(1, int(max_intents))
        raw_separators = intent_separator_tokens or _DEFAULT_INTENT_SEPARATORS
        separators: List[str] = []
        for sep in raw_separators:
            norm_sep = normalize(sep)
            if norm_sep:
                separators.append(norm_sep)
        self._intent_separator_tokens = tuple(separators)
        self._intent_separator_set = set(self._intent_separator_tokens)
        strategy = (combine_strategy or "max").lower()
        if strategy not in {"max", "sum"}:
            raise ValueError(f"combine_strategy must be 'max' or 'sum', got {combine_strategy}")
        self._combine_strategy = strategy
        self._multi_intent_bonus = float(multi_intent_bonus)

        self._sessions: Dict[str, _Session] = {}
        self._catalog: Dict[str, ToolSpec] = {}
        self._trie = Trie()
        self._term_to_tools: Dict[str, set[str]] = defaultdict(set)
        self._term_lengths: Dict[str, int] = {}
        self._inv_index = InvertedIndex()
        self._anchor_vocab: Set[str] = set()
        self._stopwords = stopwords(self._locales) if self._drop_stopwords else set()

        self.add_tools(tools)

    # --- Session API ---
    def feed(self, text_delta: str, *, session_id: str) -> List[Suggestion]:
        session = self._sessions.setdefault(session_id, _Session())
        session.buffer += text_delta
        return self._suggest(session.buffer)

    def submit(self, text: str, *, session_id: str) -> List[Suggestion]:
        self._sessions[session_id] = _Session(buffer=text)
        return self._suggest(text)

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    # --- Catalog ---
    def add_tools(self, tools: Iterable[ToolSpec]) -> None:
        for tool in tools:
            name = tool.get("name")
            if not name:
                continue
            self._catalog[name] = tool
            terms = self._extract_terms(tool)
            for term in terms:
                self._trie.insert(term)
                self._term_to_tools[term].add(name)
                self._term_lengths[term] = len(term)
            by_field = self._extract_terms_by_field(tool)
            self._inv_index.add_tool(name, by_field)
            self._anchor_vocab.update(self._anchor_terms_from_fields(by_field))

    def remove_tool(self, name: str) -> None:
        if name not in self._catalog:
            return
        del self._catalog[name]
        # Rebuild lightweight maps (simpler than incremental delete on trie)
        self._rebuild_index()

    # --- Internals ---
    def _rebuild_index(self) -> None:
        self._trie = Trie()
        self._term_to_tools = defaultdict(set)
        self._term_lengths = {}
        self._inv_index = InvertedIndex()
        self._anchor_vocab = set()
        for tool in self._catalog.values():
            terms = self._extract_terms(tool)
            for term in terms:
                self._trie.insert(term)
                self._term_to_tools[term].add(tool["name"])
                self._term_lengths[term] = len(term)
            by_field = self._extract_terms_by_field(tool)
            self._inv_index.add_tool(tool["name"], by_field)
            self._anchor_vocab.update(self._anchor_terms_from_fields(by_field))

    def _extract_terms(self, tool: ToolSpec) -> List[str]:
        terms: List[str] = []
        fields = [
            tool.get("name", ""),
            tool.get("description", ""),
        ]
        for f in fields:
            terms.extend(tokens(f))
        for key in ("keywords", "aliases"):
            for t in tool.get(key, []) or []:
                terms.extend(tokens(t))
        out = []
        for t in terms:
            nt = normalize(t)
            if nt:
                out.append(nt)
        return sorted(set(out))

    def _extract_terms_by_field(self, tool: ToolSpec) -> Dict[Field, List[str]]:
        """Return normalized tokens by field for a tool."""
        by_field: Dict[Field, List[str]] = {
            "name": tokens(tool.get("name", "")),
            "description": tokens(tool.get("description", "")),
            "keywords": [],
            "aliases": [],
        }
        for key in ("keywords", "aliases"):
            items = tool.get(key, []) or []
            for v in items:
                by_field[key].extend(tokens(v))
        for k, vals in list(by_field.items()):
            normed: List[str] = []
            for v in vals:
                nv = normalize(v)
                if nv:
                    normed.append(nv)
            by_field[k] = normed
        return by_field

    def _anchor_terms_from_fields(self, by_field: Dict[Field, List[str]]) -> Set[str]:
        terms: Set[str] = set()
        for field in self._anchor_fields:
            terms.update(by_field.get(field, []))
        return terms

    def _intent_windows(self, text: str) -> List[_IntentWindow]:
        """Return intent windows extracted from text, respecting separators and anchors."""
        stream = tokens_with_spans(
            text,
            drop_stopwords=False,
            locales=self._locales,
            remove_noise=True,
        )
        if not stream:
            return []

        normalized_text = normalize(text)

        tokens_only: List[str] = []
        is_stop_flags: List[bool] = []
        is_anchor_flags: List[bool] = []
        spans: List[Tuple[int, int]] = []
        is_separator_flags: List[bool] = []

        for tok, span in stream:
            tokens_only.append(tok)
            is_stop = self._drop_stopwords and tok in self._stopwords
            is_stop_flags.append(is_stop)
            is_anchor = tok in self._anchor_vocab
            is_anchor_flags.append(is_anchor)
            spans.append(span)
            is_separator_flags.append(tok in self._intent_separator_set)

        if not tokens_only:
            return []

        punctuation_boundaries: Set[int] = set()
        prev_end = 0
        for idx, span in enumerate(spans):
            gap = normalized_text[prev_end : span[0]]
            if any(ch in gap for ch in (",", ";")):
                punctuation_boundaries.add(idx)
            prev_end = span[1]

        segments: List[Tuple[int, int]] = []
        start = 0
        for idx, token in enumerate(tokens_only):
            if is_separator_flags[idx]:
                if start < idx:
                    segments.append((start, idx))
                start = idx + 1
                continue
            if idx in punctuation_boundaries and start < idx:
                segments.append((start, idx))
                start = idx
        if start < len(tokens_only):
            segments.append((start, len(tokens_only)))

        if not segments:
            segments = [(0, len(tokens_only))]

        windows: List[_IntentWindow] = []

        for seg_start, seg_end in segments:
            anchor_indices: List[int] = [
                idx for idx in range(seg_start, seg_end) if is_anchor_flags[idx]
            ]
            window_ranges: List[Tuple[int, int]] = []
            if anchor_indices:
                for anchor_idx in anchor_indices:
                    start_idx = max(seg_start, anchor_idx - self._window_radius)
                    end_idx = min(seg_end, anchor_idx + self._window_radius + 1)
                    if window_ranges and start_idx <= window_ranges[-1][1]:
                        prev_start, prev_end = window_ranges[-1]
                        window_ranges[-1] = (prev_start, max(prev_end, end_idx))
                    else:
                        window_ranges.append((start_idx, end_idx))
            else:
                window_ranges.append((seg_start, seg_end))

            for win_start, win_end in window_ranges:
                scoped_tokens: List[str] = []
                anchor_hits = 0
                for idx in range(win_start, win_end):
                    if is_anchor_flags[idx]:
                        anchor_hits += 1
                    if self._drop_stopwords and is_stop_flags[idx]:
                        continue
                    scoped_tokens.append(tokens_only[idx])
                if not scoped_tokens:
                    continue
                last_prefix = scoped_tokens[-1]
                complete_terms = scoped_tokens[:-1]
                windows.append(
                    _IntentWindow(
                        complete_terms=complete_terms,
                        last_prefix=last_prefix,
                        anchor_hits=anchor_hits,
                    )
                )

        if not windows:
            return []

        anchored = [win for win in windows if win.anchor_hits > 0]
        fallback = [win for win in windows if win.anchor_hits <= 0]
        ordered = anchored + fallback if anchored else fallback
        return ordered[: self._max_intents]

    def _min_complete_hits(self, anchor_hits: int, complete_terms: List[str]) -> Optional[int]:
        if complete_terms and anchor_hits:
            return max(1, int(math.ceil(anchor_hits * max(0.0, self._anchor_alpha))))
        if complete_terms:
            return max(1, int(math.ceil(len(complete_terms) * max(0.0, min(1.0, self._alpha)))))
        return None

    def _suggest(self, text: str) -> List[Suggestion]:
        windows = self._intent_windows(text)
        if not windows:
            return []

        combined: Dict[str, Dict[str, Any]] = {}
        window_top_k = self._top_k if self._max_intents <= 1 else max(
            self._top_k, self._top_k * self._max_intents
        )

        for idx, window in enumerate(windows):
            expanded_terms: Set[str] = set()
            if window.last_prefix:
                expanded_terms.update(self._trie.prefix_terms(window.last_prefix, limit=64))

            complete_terms_set = set(window.complete_terms)
            query_terms = complete_terms_set | expanded_terms
            if not query_terms:
                continue

            min_hits = self._min_complete_hits(window.anchor_hits, window.complete_terms)
            ranked = self._inv_index.query(
                complete_terms=complete_terms_set,
                expanded_terms=expanded_terms,
                require_anchor=self._require_anchor,
                anchor_fields=self._anchor_fields,
                alpha=self._alpha,
                min_score=self._min_score,
                top_k=window_top_k,
                min_complete_hits=min_hits,
                query_terms=query_terms,
            )
            if not ranked:
                continue

            decay = 1.0 / (idx + 1)
            for tool_name, score, contrib in ranked:
                entry = combined.setdefault(
                    tool_name,
                    {"score": 0.0, "reasons": defaultdict(set), "hits": 0},
                )
                if self._combine_strategy == "max":
                    entry["score"] = max(entry["score"], float(score))
                else:
                    entry["score"] += float(score) * decay
                entry["hits"] += 1
                reason_map = entry["reasons"]
                for term, fields in contrib.items():
                    field_set = reason_map.setdefault(term, set())
                    field_set.update(fields)

        if not combined:
            return []

        for entry in combined.values():
            hits = entry["hits"]
            if hits > 1 and self._multi_intent_bonus:
                entry["score"] += self._multi_intent_bonus * (hits - 1)

        ranked_tools = sorted(
            combined.items(),
            key=lambda item: item[1]["score"],
            reverse=True,
        )

        suggestions: List[Suggestion] = []
        for tool_name, data in ranked_tools[: self._top_k]:
            tool = self._catalog.get(tool_name, {"name": tool_name, "description": tool_name})
            parts = []
            for term in sorted(data["reasons"].keys()):
                fields = ",".join(sorted(data["reasons"][term]))
                parts.append(f"{term}: {fields}")
            reason = "; ".join(parts)
            suggestions.append(
                {
                    "id": tool_name,
                    "kind": "tool",
                    "score": float(data["score"]),
                    "label": tool.get("name", tool_name),
                    "reason": reason,
                    "arguments_template": {},
                    "metadata": {"tags": tool.get("tags", [])},
                }
            )

        return suggestions
