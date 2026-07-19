"""BibTeX and RIS export for reference managers (Zotero/Mendeley/EndNote).

Turns the corpus rows into ``.bib`` / ``.ris`` so a researcher can import the
retrieved records straight into a reference manager — closing the audit's
"registro recuperado → referência correspondente" link.

Like ``analysis.references``, it **never invents** bibliographic data: only
fields actually present on a row are emitted, and entries with no usable
identity (no title and no DOI/URL) are skipped rather than fabricated. Nothing
here is authoritative on its own; it re-serializes what was already captured.
"""
from __future__ import annotations

import re
from pathlib import Path

_KEY_CLEAN = re.compile(r"[^a-z0-9]+")
_WS = re.compile(r"\s+")

# BibTeX entry type / RIS type by document nature (best-effort, from article_type
# or evidence_type). Unknown → journal article (the safe, common default).
_GUIDELINE_HINTS = ("guideline", "guide", "official", "normative", "diretriz", "report", "consensus")
_REVIEW_HINTS = ("review", "revisão", "revisao", "meta-analysis", "metanalise")


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "; ".join(_text(v) for v in value if _text(v))
    return _WS.sub(" ", str(value)).strip()


def _authors_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [_text(v) for v in value if _text(v)]
    text = _text(value)
    if not text:
        return []
    # Accept the common serializations: "A; B", "A and B", or a single name.
    if ";" in text:
        parts = text.split(";")
    elif " and " in text:
        parts = text.split(" and ")
    else:
        parts = [text]
    return [p.strip() for p in parts if p.strip()]


def _year(row: dict) -> str:
    year = _text(row.get("year"))
    if year:
        match = re.search(r"(19|20)\d{2}", year)
        if match:
            return match.group(0)
    match = re.search(r"(19|20)\d{2}", _text(row.get("publication_date")))
    return match.group(0) if match else ""


def _url(row: dict) -> str:
    return _text(row.get("final_url") or row.get("original_url") or row.get("url"))


def _entry_types(row: dict) -> tuple[str, str]:
    """(bibtex_type, ris_type) inferred from the document nature."""
    hint = f"{_text(row.get('article_type'))} {_text(row.get('evidence_type'))} {_text(row.get('source_provider'))}".lower()
    if any(h in hint for h in _GUIDELINE_HINTS):
        return "techreport", "RPRT"
    if any(h in hint for h in _REVIEW_HINTS):
        return "article", "JOUR"
    return ("article", "JOUR") if _text(row.get("journal")) else ("misc", "GEN")


def _has_identity(row: dict) -> bool:
    return bool(_text(row.get("title")) or _text(row.get("doi")) or _url(row))


def citation_key(row: dict, used: set[str]) -> str:
    """A stable, unique BibTeX key: firstauthor+year+titleword, else document_id."""
    authors = _authors_list(row.get("authors"))
    author_tok = _KEY_CLEAN.sub("", authors[0].split(",")[0].lower()) if authors else ""
    year = _year(row)
    title_tok = ""
    for word in _text(row.get("title")).lower().split():
        cleaned = _KEY_CLEAN.sub("", word)
        if len(cleaned) >= 4:
            title_tok = cleaned
            break
    base = "".join(t for t in (author_tok, year, title_tok) if t)
    if not base:
        base = _KEY_CLEAN.sub("", _text(row.get("document_id")).lower()) or "ref"
    key = base
    i = 2
    while key in used:
        key = f"{base}_{i}"
        i += 1
    used.add(key)
    return key


def _bib_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def to_bibtex(rows: list[dict]) -> str:
    """Serialize rows as a BibTeX bibliography (only fields actually present)."""
    used: set[str] = set()
    entries: list[str] = []
    for row in rows:
        if not _has_identity(row):
            continue
        btype, _ = _entry_types(row)
        key = citation_key(row, used)
        fields: list[tuple[str, str]] = []
        if _text(row.get("title")):
            fields.append(("title", _text(row.get("title"))))
        authors = _authors_list(row.get("authors"))
        if authors:
            fields.append(("author", " and ".join(authors)))
        journal = _text(row.get("journal"))
        if journal:
            fields.append(("journal" if btype == "article" else "institution", journal))
        institution = _text(row.get("source_institution") or row.get("issuing_body"))
        if institution and btype == "techreport" and not journal:
            fields.append(("institution", institution))
        if _year(row):
            fields.append(("year", _year(row)))
        if _text(row.get("doi")):
            fields.append(("doi", _text(row.get("doi"))))
        if _url(row):
            fields.append(("url", _url(row)))
        note = _text(row.get("country"))
        if note:
            fields.append(("addendum", note))
        body = ",\n".join(f"  {name} = {{{_bib_escape(val)}}}" for name, val in fields)
        entries.append(f"@{btype}{{{key},\n{body}\n}}")
    return "\n\n".join(entries) + ("\n" if entries else "")


def to_ris(rows: list[dict]) -> str:
    """Serialize rows as an RIS bibliography (only fields actually present)."""
    blocks: list[str] = []
    for row in rows:
        if not _has_identity(row):
            continue
        _, rtype = _entry_types(row)
        lines: list[str] = [f"TY  - {rtype}"]
        if _text(row.get("title")):
            lines.append(f"TI  - {_text(row.get('title'))}")
        for author in _authors_list(row.get("authors")):
            lines.append(f"AU  - {author}")
        journal = _text(row.get("journal"))
        if journal:
            lines.append(f"JO  - {journal}")
        if _year(row):
            lines.append(f"PY  - {_year(row)}")
        if _text(row.get("doi")):
            lines.append(f"DO  - {_text(row.get('doi'))}")
        if _url(row):
            lines.append(f"UR  - {_url(row)}")
        if _text(row.get("abstract")):
            lines.append(f"AB  - {_text(row.get('abstract'))}")
        lines.append("ER  - ")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def write_bibtex(rows: list[dict], path: Path) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_bibtex(rows), encoding="utf-8")
    return sum(1 for r in rows if _has_identity(r))


def write_ris(rows: list[dict], path: Path) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_ris(rows), encoding="utf-8")
    return sum(1 for r in rows if _has_identity(r))
