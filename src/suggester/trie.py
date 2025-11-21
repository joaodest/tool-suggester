from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set


@dataclass
class TrieNode:
    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    terminal: bool = False
    terms: Set[str] = field(default_factory=set)
    # descendant terms for prefix search
    desc_terms: Set[str] = field(default_factory=set)


class Trie:
    """Character trie for complete terms.

    Each inserted term is added as terminal; we maintain `desc_terms` to
    quickly return all terms that share a prefix.
    """

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, term: str) -> None:
        node = self.root
        node.desc_terms.add(term)
        for ch in term:
            node = node.children.setdefault(ch, TrieNode())
            node.desc_terms.add(term)
        node.terminal = True
        node.terms.add(term)

    def bulk_insert(self, terms: Iterable[str]) -> None:
        for t in terms:
            if t:
                self.insert(t)

    def prefix_terms(self, prefix: str, *, limit: Optional[int] = None) -> List[str]:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        terms = list(node.desc_terms)
        if limit is not None:
            return terms[:limit]
        return terms

