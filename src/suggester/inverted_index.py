from __future__ import annotations

import math
from collections import defaultdict
from typing import DefaultDict, Dict, Iterable, List, MutableMapping, Optional, Sequence, Set, Tuple


Field = str  # expected values: "name", "keywords", "aliases", "description"


class InvertedIndex:
    """Inverted index over tool terms with field-aware postings and simple TF‑IDF.

    Data model:
    - term_to_tools[term][tool_id][field] = tf (int)
    - df[term] = number of unique tools containing the term
    - tools: set of tool_ids registered (for N in idf)

    Field weights default: name=3.0, keywords=2.0, aliases=1.8, description=1.0
    """

    def __init__(self, field_weights: MutableMapping[Field, float] | None = None) -> None:
        self.term_to_tools: Dict[str, Dict[str, Dict[Field, int]]] = {}
        self.df: Dict[str, int] = {}
        self.tools: Set[str] = set()
        self.field_weights: Dict[Field, float] = {
            "name": 3.0,
            "keywords": 2.0,
            "aliases": 1.8,
            "description": 1.0,
        }
        if field_weights:
            self.field_weights.update(dict(field_weights))

    # --- Build ---
    def add_tool(self, tool_id: str, terms_by_field: Dict[Field, Iterable[str]]) -> None:
        """Add a tool to the index using pre-tokenized terms by field."""
        self.tools.add(tool_id)

        # compute tf per term per field for this tool
        per_field_counts: Dict[Field, Dict[str, int]] = {}
        for field, terms in terms_by_field.items():
            counts: DefaultDict[str, int] = defaultdict(int)
            for t in terms:
                if not t:
                    continue
                counts[t] += 1
            if counts:
                per_field_counts[field] = dict(counts)

        # update postings and df (per tool unique)
        seen_terms_for_df: Set[str] = set()
        for field, counts in per_field_counts.items():
            for term, tf in counts.items():
                tool_map = self.term_to_tools.setdefault(term, {})
                field_map = tool_map.setdefault(tool_id, {})
                field_map[field] = field_map.get(field, 0) + tf
                if term not in seen_terms_for_df:
                    self.df[term] = self.df.get(term, 0) + 1
                    seen_terms_for_df.add(term)

    # --- Query ---
    def _idf(self, term: str) -> float:
        N = len(self.tools)
        df = self.df.get(term, 0)
        return 1.0 + math.log((1 + N) / (1 + df + 1e-9))

    def query(
        self,
        *,
        complete_terms: Set[str],
        expanded_terms: Set[str],
        require_anchor: bool = True,
        anchor_fields: Sequence[Field] = ("name", "keywords", "aliases"),
        alpha: float = 0.6,
        min_score: float = 1.0,
        top_k: int = 3,
        min_complete_hits: Optional[int] = None,
        query_terms: Optional[Set[str]] = None,
    ) -> List[Tuple[str, float, Dict[str, List[Field]]]]:
        """Return ranked tools for the given query terms.

        - complete_terms: tokens fully typed by the user (used for intersection threshold)
        - expanded_terms: expansions for the last prefix via trie
        - require_anchor: at least one matched term must come from an anchor field
        - alpha: fraction of complete_terms that must be matched by a tool
        - returns: list of (tool_id, score, contributions {term: [fields...]})
        """
        if query_terms is not None:
            query_terms = set(query_terms)
        else:
            query_terms = set(complete_terms) | set(expanded_terms)
        if not query_terms:
            return []

        # gather candidate tools
        candidates: Set[str] = set()
        for term in query_terms:
            tmap = self.term_to_tools.get(term)
            if tmap:
                candidates.update(tmap.keys())

        if min_complete_hits is not None:
            required = max(0, int(min_complete_hits))
        else:
            required = int(math.ceil(len(complete_terms) * max(0.0, min(1.0, alpha))))
        results: List[Tuple[str, float, Dict[str, List[Field]]]] = []

        for tool_id in candidates:
            contributions: Dict[str, List[Field]] = {}
            score = 0.0
            matched_complete = 0
            anchor_hit = False

            for term in query_terms:
                tmap = self.term_to_tools.get(term)
                if not tmap:
                    continue
                fmap = tmap.get(tool_id)
                if not fmap:
                    continue

                # track fields for explaining
                for field, tf in fmap.items():
                    if field in anchor_fields:
                        anchor_hit = True
                    # scoring
                    score += float(tf) * self.field_weights.get(field, 1.0) * self._idf(term)
                    contributions.setdefault(term, [])
                    if field not in contributions[term]:
                        contributions[term].append(field)

                # count matched complete terms
                if term in complete_terms:
                    matched_complete += 1

            if require_anchor and not anchor_hit:
                continue
            if matched_complete < required:
                continue
            if score < float(min_score):
                continue

            results.append((tool_id, score, contributions))

        results.sort(key=lambda x: x[1], reverse=True)
        if top_k is not None and top_k > 0:
            results = results[:top_k]
        return results
