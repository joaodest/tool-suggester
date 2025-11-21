from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Sequence, Set, Tuple


_WORD = re.compile(r"\w+", re.UNICODE)

# Minimal multilingual stopword lists (extendable via locales).
_STOPWORDS = {
    "pt": {
        "a",
        "o",
        "os",
        "as",
        "de",
        "do",
        "da",
        "das",
        "dos",
        "pra",
        "para",
        "por",
        "que",
        "com",
        "e",
        "eu",
        "me",
        "meu",
        "minha",
        "meus",
        "minhas",
        "em",
        "um",
        "uma",
        "uns",
        "umas",
        "no",
        "na",
        "nos",
        "nas",
        "ao",
        "aos",
        "vou",
        "quero",
        "preciso",
        "gostaria",
        "desejo",
        "favor",
    },
    "en": {
        "a",
        "an",
        "the",
        "to",
        "for",
        "with",
        "and",
        "or",
        "but",
        "i",
        "me",
        "my",
        "you",
        "want",
        "would",
        "like",
        "need",
        "please",
        "from",
        "on",
        "in",
        "at",
        "of",
    },
}


def _normalize_locale(locale: str) -> str:
    if not locale:
        return ""
    return locale.split("-")[0].lower()


def stopwords(locales: Sequence[str] | None = None) -> Set[str]:
    """Return stopwords for the provided locales (language codes)."""
    locales = locales or ("pt", "en")
    acc: Set[str] = set()
    for loc in locales:
        bucket = _STOPWORDS.get(_normalize_locale(loc))
        if bucket:
            acc.update(bucket)
    return acc


def _is_noise(token: str) -> bool:
    if not token:
        return True
    if token.isdigit():
        return True
    if len(token) == 1 and not token.isalpha():
        return True
    if len(set(token)) == 1 and len(token) >= 4:
        return True
    return False


def normalize(text: str) -> str:
    """Normalize text: lowercase, strip accents, trim whitespace.

    - Lowercases
    - Removes diacritics (NFKD)
    - Collapses whitespace
    """
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = " ".join(text.split())
    return text


def tokens_with_spans(
    text: str,
    *,
    drop_stopwords: bool = False,
    locales: Sequence[str] = ("pt", "en"),
    remove_noise: bool = True,
    extra_stopwords: Iterable[str] | None = None,
) -> List[Tuple[str, Tuple[int, int]]]:
    """Return tokens and their (start, end) spans in original text after normalization.

    Note: spans are relative to the normalized string returned by normalize().
    """
    norm = normalize(text)
    stopword_set: Set[str] = set()
    if drop_stopwords:
        stopword_set.update(stopwords(locales))
        if extra_stopwords:
            stopword_set.update(extra_stopwords)

    items: List[Tuple[str, Tuple[int, int]]] = []
    for match in _WORD.finditer(norm):
        tok = match.group(0)
        if remove_noise and _is_noise(tok):
            continue
        if drop_stopwords and tok in stopword_set:
            continue
        items.append((tok, match.span()))
    return items


def tokens(
    text: str,
    *,
    drop_stopwords: bool = False,
    locales: Sequence[str] = ("pt", "en"),
    remove_noise: bool = True,
    extra_stopwords: Iterable[str] | None = None,
) -> List[str]:
    """Convenience helper returning tokens only."""
    return [
        tok
        for tok, _ in tokens_with_spans(
            text,
            drop_stopwords=drop_stopwords,
            locales=locales,
            remove_noise=remove_noise,
            extra_stopwords=extra_stopwords,
        )
    ]
