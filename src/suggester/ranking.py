from __future__ import annotations

from typing import Dict

def lexical_score(term_counts: Dict[str, int], term_lengths: Dict[str, int]) -> float:
    """Compute a simple lexical score.

    Score = sum(count * (1 + len(term)/8)) across matched terms.
    """
    score = 0.0
    for term, count in term_counts.items():
        score += count * (1.0 + term_lengths.get(term, 0) / 8.0)
    return score


def rank_tools(
    tool_term_counts: Dict[str, Dict[str, int]],
    term_lengths: Dict[str, int],
) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for tool, tcounts in tool_term_counts.items():
        scores[tool] = lexical_score(tcounts, term_lengths)
    return scores

