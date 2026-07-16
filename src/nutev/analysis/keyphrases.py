"""Key-phrase / key-sentence extraction from a document's full text.

The A/B/C/D coding in :mod:`nutev.analysis.article1_coding` decides *whether* a
domain is present; this module surfaces *which sentences say so* — the "frases
chave" a human reviewer reads to confirm the coding — plus the document's most
frequent meaningful terms.

It is deliberately dependency-free (no NLP model), reuses the same domain
keywords and actionable cues as the coder (so the phrases match the coding), and
never fabricates: every returned sentence is a verbatim span of the input text.
The output is assistive and enters human review like the rest of the coding.
"""
from __future__ import annotations

import re
from collections import Counter

from nutev.analysis.article1_coding import _ACTIONABLE_CUES, _DOMAIN_KEYWORDS

# Sentence boundary: end punctuation followed by whitespace, or a newline block.
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n{1,}")
_WS = re.compile(r"\s+")
_WORD = re.compile(r"[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ'\-]{2,}")

# Minimal EN+PT stop list — enough to keep top_terms meaningful without a heavy
# NLP dependency. Not exhaustive by design.
_STOPWORDS = {
    # English
    "the", "and", "for", "are", "with", "that", "this", "from", "have", "has",
    "not", "was", "were", "will", "can", "should", "may", "such", "these", "those",
    "which", "their", "they", "than", "then", "also", "into", "more", "most",
    "other", "some", "been", "being", "over", "under", "between", "about", "each",
    "when", "where", "what", "who", "how", "all", "any", "but", "our", "its",
    # Portuguese
    "que", "com", "para", "por", "uma", "dos", "das", "como", "mais", "não",
    "nao", "seu", "sua", "ser", "está", "esta", "este", "isso", "pelo", "pela",
    "são", "sao", "foi", "aos", "nas", "nos", "num", "numa", "entre", "sobre",
    "quando", "onde", "pode", "deve", "cada", "todos", "todas", "essa", "esse",
}


def split_sentences(text: str) -> list[str]:
    """Split ``text`` into trimmed, non-empty sentences."""
    if not text:
        return []
    parts = _SENT_SPLIT.split(text)
    out: list[str] = []
    for part in parts:
        s = _WS.sub(" ", part).strip()
        if s:
            out.append(s)
    return out


def extract_keyphrases(text: str, *, max_per_domain: int = 5) -> list[dict]:
    """Return the domain-relevant key sentences from ``text``.

    For each A/B/C/D domain, finds sentences that contain a domain keyword and
    ranks those that also carry an actionable cue (recommend/should/…) higher —
    the same substantive signal the coder uses. Returns up to ``max_per_domain``
    per domain, each as ``{"domain", "actionable", "sentence"}``. Sentences are
    verbatim spans, deduplicated across domains.
    """
    sentences = split_sentences(text)
    out: list[dict] = []
    seen: set[str] = set()
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        scored: list[tuple[int, str]] = []
        for sentence in sentences:
            low = sentence.lower()
            if any(kw in low for kw in keywords):
                actionable_hits = sum(1 for cue in _ACTIONABLE_CUES if cue in low)
                scored.append((actionable_hits, sentence))
        # Actionable sentences first; then shorter (more quotable) ones.
        scored.sort(key=lambda x: (-x[0], len(x[1])))
        taken = 0
        for actionable_hits, sentence in scored:
            fingerprint = sentence.strip().lower()[:160]
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            out.append({
                "domain": domain,
                "actionable": actionable_hits > 0,
                "sentence": sentence.strip(),
            })
            taken += 1
            if taken >= max_per_domain:
                break
    return out


def extract_keyphrases_from_pages(pages: list[str], *, max_per_domain: int = 5) -> list[dict]:
    """Like :func:`extract_keyphrases` but records the 1-indexed ``page`` of each
    key sentence, for page-precise citation. ``pages`` is per-page text (OCR or
    native); an empty/whitespace page is skipped.
    """
    # Tag every sentence with its source page, then reuse the same ranking.
    sentences_with_page: list[tuple[int, str]] = []
    for page_no, page_text in enumerate(pages, start=1):
        for sentence in split_sentences(page_text or ""):
            sentences_with_page.append((page_no, sentence))

    out: list[dict] = []
    seen: set[str] = set()
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        scored: list[tuple[int, int, str]] = []
        for page_no, sentence in sentences_with_page:
            low = sentence.lower()
            if any(kw in low for kw in keywords):
                actionable_hits = sum(1 for cue in _ACTIONABLE_CUES if cue in low)
                scored.append((actionable_hits, page_no, sentence))
        scored.sort(key=lambda x: (-x[0], len(x[2])))
        taken = 0
        for actionable_hits, page_no, sentence in scored:
            fingerprint = sentence.strip().lower()[:160]
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            out.append({
                "domain": domain,
                "actionable": actionable_hits > 0,
                "sentence": sentence.strip(),
                "page": page_no,
            })
            taken += 1
            if taken >= max_per_domain:
                break
    return out


def top_terms(text: str, *, n: int = 15, min_len: int = 4) -> list[str]:
    """Return the ``n`` most frequent meaningful terms (stop-word filtered)."""
    if not text:
        return []
    counts: Counter[str] = Counter()
    for match in _WORD.findall(text.lower()):
        if len(match) >= min_len and match not in _STOPWORDS:
            counts[match] += 1
    return [term for term, _ in counts.most_common(n)]


def keyphrase_fields(record: dict, *, max_per_domain: int = 5, n_terms: int = 15) -> dict:
    """Compute flat key-phrase fields for a metadata row.

    Reads ``extracted_text`` (falling back to title+abstract) and returns:
    ``key_phrases`` (list of dicts), ``key_phrases_text`` (a human-readable
    ``[A] sentence`` block for the CSV), ``n_key_phrases`` and ``top_terms``
    (pipe-joined). Empty text yields empty fields — never an error.
    """
    text = str(
        record.get("extracted_text")
        or " ".join(str(record.get(k, "") or "") for k in ("title", "abstract"))
        or ""
    )
    phrases = extract_keyphrases(text, max_per_domain=max_per_domain)
    terms = top_terms(text, n=n_terms)
    readable = "\n".join(f"[{p['domain']}] {p['sentence']}" for p in phrases)
    return {
        "key_phrases": phrases,
        "key_phrases_text": readable,
        "n_key_phrases": len(phrases),
        "top_terms": "|".join(terms),
    }
