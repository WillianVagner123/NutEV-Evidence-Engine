"""Deterministic question-to-search-strategy planner.

A person types a question or keywords (Portuguese or English). The planner
recognises concepts from the curated vocabulary in ``config/query_vocabulary.json``,
organises them into PICO-style blocks (population, intervention, comparator,
context, outcome, study design and free terms), extracts year limits and then
compiles one query string per source in that source's own syntax.

Guardrails:

* no language model and no network: the same input always yields the same plan;
* every block, term and string is shown to the user, who may edit it;
* MeSH/DeCS headings are never invented: free-text synonyms come from the curated
  vocabulary, and controlled-vocabulary expansion is left to the source itself
  (PubMed automatic term mapping, Europe PMC synonyms) only in ``broad`` mode;
* a typed Boolean/field-tagged string is passed through literally (manual mode);
* the plan describes how to search; it is not eligibility, quality or PRISMA.

The browser port lives in ``apps/nutev-open/planner.js`` and is verified against
this module by ``nutev_tests/test_question_planner.py``.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import re
from typing import Any

from nutev.taxonomy import _norm

PLANNER_VERSION = "nutev-question-planner-v2"
QUERY_VOCABULARY_FILENAME = "query_vocabulary.json"
FIELD_MODES = ("title_abstract", "broad")
LIVE_PROVIDERS = ("europepmc", "pubmed", "openalex", "crossref")
LINK_PROVIDERS = ("bvs_lilacs", "scielo")
ROLES = ("population", "intervention", "comparator", "context", "outcome", "design", "free")
MAX_QUESTION_LENGTH = 500
MAX_BLOCKS_WARNING = 5
MAX_CROSSREF_WORDS = 14

_PUBMED_TAG_RE = re.compile(r"\[[A-Za-z /-]+\]")
_BOOLEAN_RE = re.compile(r"\b(AND|OR|NOT)\b|\[[A-Za-z /-]+\]|\"|\b[A-Z_]{2,}:|\b(?:tw|mh|ti|ab|au):")
_NUMBER_WORDS = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6,
    "sete": 7, "oito": 8, "nove": 9, "dez": 10, "quinze": 15, "vinte": 20,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20,
}
_FROM_MARKERS: tuple[tuple[str, ...], ...] = (("desde",), ("a", "partir", "de"), ("apos",), ("depois", "de"), ("since",), ("from",), ("after",))
_TO_MARKERS: tuple[tuple[str, ...], ...] = (("ate",), ("until",), ("through",))
_BEFORE_MARKERS: tuple[tuple[str, ...], ...] = (("antes", "de"), ("before",))
_RANGE_START: tuple[tuple[str, ...], ...] = (("entre",), ("between",), ("de",), ("from",))
_RANGE_JOIN: tuple[tuple[str, ...], ...] = (("e",), ("and",), ("a",), ("to",), ("ate",))
_LAST_MARKERS: tuple[tuple[str, ...], ...] = (("ultimos",), ("nos", "ultimos"), ("last",), ("past",), ("the", "last"), ("the", "past"))
_YEAR_UNITS = ("anos", "ano", "years", "year")
_ENCODE_SAFE = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.!~*'()")


class QueryVocabularyError(RuntimeError):
    """Raised when the curated query vocabulary is invalid."""


def stem(token: str) -> str:
    """Light, symmetric plural folding used only for trigger matching."""

    return token[:-1] if len(token) > 4 and token.endswith("s") else token


def tokens_of(text: Any) -> list[str]:
    normalized = _norm(text)
    return normalized.split(" ") if normalized else []


def encode_component(value: str) -> str:
    """Percent-encode exactly like JavaScript ``encodeURIComponent``."""

    out: list[str] = []
    for char in str(value):
        if char in _ENCODE_SAFE:
            out.append(char)
        else:
            out.extend(f"%{byte:02X}" for byte in char.encode("utf-8"))
    return "".join(out)


def _query_string(params: Mapping[str, str]) -> str:
    return "&".join(f"{encode_component(key)}={encode_component(value)}" for key, value in params.items())


# ---------------------------------------------------------------------------- vocabulary


def load_query_vocabulary(config_dir: Path) -> dict[str, Any]:
    path = Path(config_dir) / QUERY_VOCABULARY_FILENAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QueryVocabularyError(f"Cannot read {path}: {exc}") from exc
    validate_query_vocabulary(data)
    return data


def validate_query_vocabulary(data: Any, taxonomy_groups: set[str] | None = None) -> None:
    if not isinstance(data, dict):
        raise QueryVocabularyError("Vocabulary must be a JSON object")
    roles = data.get("roles")
    if not isinstance(roles, dict) or set(roles) != set(ROLES):
        raise QueryVocabularyError(f"roles must define exactly {ROLES}")
    concepts = data.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        raise QueryVocabularyError("Vocabulary needs a non-empty concepts list")
    seen_ids: set[str] = set()
    seen_triggers: dict[tuple[str, ...], str] = {}
    for concept in concepts:
        concept_id = str(concept.get("id") or "")
        if not concept_id or concept_id in seen_ids:
            raise QueryVocabularyError(f"Missing or duplicated concept id: {concept_id!r}")
        seen_ids.add(concept_id)
        if concept.get("role") not in ROLES or concept.get("role") in {"comparator", "free"}:
            raise QueryVocabularyError(f"{concept_id}: invalid role {concept.get('role')!r}")
        for key in ("label_pt", "label_en"):
            if not str(concept.get(key) or "").strip():
                raise QueryVocabularyError(f"{concept_id}: missing {key}")
        if not concept.get("en"):
            raise QueryVocabularyError(f"{concept_id}: needs at least one English search term")
        for term in [*concept.get("en", []), *concept.get("pt", [])]:
            text = str(term).strip()
            if not text or '"' in text or (text.endswith("*") and " " in text):
                raise QueryVocabularyError(f"{concept_id}: invalid search term {term!r}")
        group = concept.get("taxonomy_group")
        if group is not None and taxonomy_groups is not None and group not in taxonomy_groups:
            raise QueryVocabularyError(f"{concept_id}: unknown taxonomy_group {group}")
        triggers = concept.get("triggers") or []
        if not triggers:
            raise QueryVocabularyError(f"{concept_id}: needs triggers")
        for trigger in triggers:
            trigger_key = tuple(stem(token) for token in tokens_of(trigger))
            if not trigger_key:
                raise QueryVocabularyError(f"{concept_id}: empty trigger {trigger!r}")
            owner = seen_triggers.get(trigger_key)
            if owner and owner != concept_id:
                raise QueryVocabularyError(
                    f"Trigger {trigger!r} is ambiguous between {owner} and {concept_id}"
                )
            seen_triggers[trigger_key] = concept_id


def _trigger_index(vocabulary: Mapping[str, Any]) -> dict[str, list[tuple[tuple[str, ...], str]]]:
    index: dict[str, list[tuple[tuple[str, ...], str]]] = {}
    for concept in vocabulary["concepts"]:
        for trigger in concept["triggers"]:
            key = tuple(stem(token) for token in tokens_of(trigger))
            entries = index.setdefault(key[0], [])
            if (key, concept["id"]) not in entries:
                entries.append((key, concept["id"]))
    for entries in index.values():
        entries.sort(key=lambda item: (-len(item[0]), item[1]))
    return index


def _marker_list(raw: list[str]) -> list[tuple[str, ...]]:
    markers = [tuple(tokens_of(value)) for value in raw]
    return sorted((m for m in markers if m), key=lambda m: (-len(m), m))


# ---------------------------------------------------------------------------- planning


def looks_like_boolean(question: str) -> bool:
    return bool(_BOOLEAN_RE.search(question))


def _match_at(tokens: list[str], index: int, sequence: tuple[str, ...]) -> bool:
    return tuple(tokens[index : index + len(sequence)]) == sequence


def _year_value(token: str, current_year: int) -> int | None:
    if len(token) == 4 and token.isdigit():
        year = int(token)
        if 1900 <= year <= current_year + 1:
            return year
    return None


def _extract_years(
    tokens: list[str], consumed: list[bool], current_year: int
) -> tuple[int | None, int | None]:
    year_from: int | None = None
    year_to: int | None = None
    n = len(tokens)

    def free(start: int, end: int) -> bool:
        return end <= n and not any(consumed[start:end])

    def take(start: int, end: int) -> None:
        for position in range(start, end):
            consumed[position] = True

    i = 0
    while i < n:
        handled = False
        for marker in _LAST_MARKERS:
            end = i + len(marker)
            if free(i, end + 2) and _match_at(tokens, i, marker) and tokens[end + 1] in _YEAR_UNITS:
                raw = tokens[end]
                amount = int(raw) if raw.isdigit() else _NUMBER_WORDS.get(raw)
                if amount and 0 < amount <= 100:
                    year_from = current_year - amount
                    take(i, end + 2)
                    i = end + 2
                    handled = True
                    break
        if handled:
            continue
        for marker in _RANGE_START:
            end = i + len(marker)
            if not (free(i, end + 1) and _match_at(tokens, i, marker)):
                continue
            first = _year_value(tokens[end], current_year) if end < n else None
            if first is None:
                continue
            for join in _RANGE_JOIN:
                join_end = end + 1 + len(join)
                if free(end + 1, join_end + 1) and _match_at(tokens, end + 1, join) and join_end < n:
                    second = _year_value(tokens[join_end], current_year)
                    if second is not None:
                        year_from, year_to = min(first, second), max(first, second)
                        take(i, join_end + 1)
                        i = join_end + 1
                        handled = True
                        break
            if handled:
                break
        if handled:
            continue
        marker_groups: tuple[tuple[tuple[tuple[str, ...], ...], str], ...] = (
            (_FROM_MARKERS, "from"),
            (_TO_MARKERS, "to"),
            (_BEFORE_MARKERS, "before"),
        )
        for markers, kind in marker_groups:
            for marker in markers:
                end = i + len(marker)
                if free(i, end + 1) and _match_at(tokens, i, marker) and end < n:
                    year = _year_value(tokens[end], current_year)
                    if year is None:
                        continue
                    if kind == "from":
                        year_from = year
                    elif kind == "to":
                        year_to = year
                    else:
                        year_to = year - 1
                    take(i, end + 1)
                    i = end + 1
                    handled = True
                    break
            if handled:
                break
        if handled:
            continue
        first = _year_value(tokens[i], current_year) if not consumed[i] else None
        second = _year_value(tokens[i + 1], current_year) if i + 1 < n and not consumed[i + 1] else None
        if first is not None and second is not None:
            year_from, year_to = min(first, second), max(first, second)
            take(i, i + 2)
            i += 2
            continue
        i += 1
    return year_from, year_to


def _dedupe_terms(terms: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, str]] = []
    for term in terms:
        key = (term["lang"], term["text"].casefold())
        if key in seen:
            continue
        seen.add(key)
        output.append(term)
    return output


def plan_question(
    question: Any,
    vocabulary: Mapping[str, Any],
    *,
    taxonomy_groups: Mapping[str, list[str]] | None = None,
    current_year: int,
    detect_manual: bool = True,
) -> dict[str, Any]:
    """Build an editable, explainable search plan from a free-text question.

    With ``detect_manual`` a typed Boolean/field-tagged string is kept literally;
    pass ``False`` to interpret it as a plain question anyway.
    """

    text = re.sub(r"\s+", " ", str(question or "")).strip()[:MAX_QUESTION_LENGTH]
    base: dict[str, Any] = {
        "planner_version": PLANNER_VERSION,
        "vocabulary_version": vocabulary.get("vocabulary_version"),
        "question": text,
        "normalized": _norm(text),
        "mode": "planned",
        "year_from": None,
        "year_to": None,
        "blocks": [],
        "dropped_terms": [],
        "warnings": [],
    }
    if not text:
        base["warnings"].append({"code": "empty_question"})
        return base
    if detect_manual and looks_like_boolean(text):
        base["mode"] = "manual"
        base["warnings"].append({"code": "manual_string"})
        if _PUBMED_TAG_RE.search(text):
            base["warnings"].append({"code": "manual_pubmed_tags"})
        return base

    tokens = tokens_of(text)
    stems = [stem(token) for token in tokens]
    consumed = [False] * len(tokens)
    year_from, year_to = _extract_years(tokens, consumed, current_year)
    base["year_from"], base["year_to"] = year_from, year_to

    concepts = {concept["id"]: concept for concept in vocabulary["concepts"]}
    index = _trigger_index(vocabulary)
    stopwords = {
        _norm(word)
        for words in (vocabulary.get("stopwords") or {}).values()
        for word in words
    }
    comparator_markers = _marker_list(list(vocabulary.get("comparator_markers") or []))

    marker_ends: set[int] = set()
    for position in range(len(tokens)):
        if consumed[position]:
            continue
        for marker in comparator_markers:
            end = position + len(marker)
            if _match_at(tokens, position, marker) and not any(consumed[position:end]):
                for covered in range(position, end):
                    consumed[covered] = True
                marker_ends.add(end)
                break

    matches: list[dict[str, Any]] = []
    i = 0
    while i < len(tokens):
        if consumed[i]:
            i += 1
            continue
        found = None
        for trigger_key, concept_id in index.get(stems[i], []):
            end = i + len(trigger_key)
            if tuple(stems[i:end]) == trigger_key and not any(consumed[i:end]):
                found = (end, concept_id)
                break
        if found is None:
            i += 1
            continue
        end, concept_id = found
        comparator = False
        probe = i
        while probe > 0 and probe not in marker_ends and tokens[probe - 1] in stopwords and not consumed[probe - 1]:
            probe -= 1
        if probe in marker_ends:
            comparator = True
        matches.append(
            {
                "concept_id": concept_id,
                "start": i,
                "text": " ".join(tokens[i:end]),
                "comparator": comparator,
            }
        )
        for covered in range(i, end):
            consumed[covered] = True
        i = end

    runs: list[tuple[int, str]] = []
    dropped: list[str] = []
    current: list[str] = []
    current_start = 0
    for position, token in enumerate(tokens):
        keep = (
            not consumed[position]
            and token not in stopwords
            and not token.isdigit()
            and len(token) >= 3
        )
        if keep:
            if not current:
                current_start = position
            current.append(token)
            continue
        if not consumed[position]:
            dropped.append(token)
        if current:
            runs.append((current_start, " ".join(current)))
            current = []
    if current:
        runs.append((current_start, " ".join(current)))
    base["dropped_terms"] = dropped

    merge_roles = set(vocabulary.get("merge_roles") or [])
    blocks: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for match in matches:
        concept = concepts[match["concept_id"]]
        role = "comparator" if match["comparator"] else concept["role"]
        if role in merge_roles:
            key = role
        else:
            key = f"{role}:{concept.get('merge_key') or concept['id']}"
        block = blocks.get(key)
        if block is None:
            block = {
                "key": key,
                "role": role,
                "concept_ids": [],
                "labels_pt": [],
                "labels_en": [],
                "matched": [],
                "taxonomy_groups": [],
                "enabled": True,
                "terms": [],
                "pubmed_filters": [],
                "source": "vocabulary",
                "position": match["start"],
                "_defaults": [],
            }
            blocks[key] = block
            order.append(key)
        if concept["id"] not in block["concept_ids"]:
            block["concept_ids"].append(concept["id"])
            block["labels_pt"].append(concept["label_pt"])
            block["labels_en"].append(concept["label_en"])
            block["_defaults"].append(bool(concept.get("default_enabled", True)))
            group = concept.get("taxonomy_group")
            if group and group not in block["taxonomy_groups"]:
                block["taxonomy_groups"].append(group)
            block["terms"].extend({"text": t, "lang": "en"} for t in concept["en"])
            block["terms"].extend({"text": t, "lang": "pt"} for t in concept.get("pt", []))
            for item in concept.get("pubmed_filters", []):
                if item not in block["pubmed_filters"]:
                    block["pubmed_filters"].append(item)
        if match["text"] not in block["matched"]:
            block["matched"].append(match["text"])

    taxonomy_terms: list[tuple[str, str]] = []
    for group, terms in (taxonomy_groups or {}).items():
        taxonomy_terms.extend((term, group) for term in terms if len(term) >= 4)
    taxonomy_terms.sort(key=lambda item: (-len(item[0]), item[0], item[1]))

    # Unknown words become one block each: the sources then combine them with AND,
    # as a plain keyword search would, instead of demanding them as one exact phrase.
    for start, run in runs:
        for offset, word in enumerate(run.split(" ")):
            key = f"free:{word}"
            if key in blocks:
                continue
            group = next((g for term, g in taxonomy_terms if term == word), None)
            blocks[key] = {
                "key": key,
                "role": "free",
                "concept_ids": [],
                "labels_pt": [word],
                "labels_en": [word],
                "matched": [word],
                "taxonomy_groups": [group] if group else [],
                "enabled": True,
                "terms": [{"text": word, "lang": "any"}],
                "pubmed_filters": [],
                "source": "free_text",
                "position": start + offset,
                "_defaults": [True],
            }
            order.append(key)

    role_order = {role: int(vocabulary["roles"][role]["order"]) for role in ROLES}
    output: list[dict[str, Any]] = []
    for key in sorted(order, key=lambda k: (role_order[blocks[k]["role"]], blocks[k]["position"], k)):
        block = blocks[key]
        defaults = block.pop("_defaults")
        block["enabled"] = block["role"] != "comparator" and any(defaults)
        block["terms"] = _dedupe_terms(block["terms"])
        block["label_pt"] = " / ".join(block.pop("labels_pt"))
        block["label_en"] = " / ".join(block.pop("labels_en"))
        output.append(block)
    base["blocks"] = output

    warnings = base["warnings"]
    if not output:
        warnings.append({"code": "nothing_recognised"})
    elif all(block["source"] == "free_text" for block in output):
        warnings.append({"code": "no_vocabulary_concepts"})
    for block in output:
        if block["role"] == "comparator":
            warnings.append({"code": "comparator_disabled", "block": block["key"]})
        elif not block["enabled"]:
            warnings.append({"code": "default_disabled", "block": block["key"]})
    enabled = sum(1 for block in output if block["enabled"])
    if enabled > MAX_BLOCKS_WARNING:
        warnings.append({"code": "many_blocks", "count": enabled})
    return base


# ---------------------------------------------------------------------------- compilation


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace('"', " ").replace(",", " ")).strip()


def _is_truncated(text: str) -> bool:
    return text.endswith("*") and " " not in text and len(text) >= 5


def _format_term(text: str, provider: str, field_mode: str) -> str:
    cleaned = _clean(text)
    if not cleaned:
        return ""
    truncated = _is_truncated(cleaned)
    bare = cleaned.rstrip("*") if not truncated else cleaned
    if provider == "pubmed":
        if field_mode == "title_abstract":
            return f"{cleaned}[tiab]" if truncated else f'"{bare}"[tiab]'
        return cleaned if truncated else (f"({bare})" if " " in bare else bare)
    if provider == "europepmc":
        if field_mode == "title_abstract":
            return f"TITLE_ABS:{cleaned}" if truncated else f'TITLE_ABS:"{bare}"'
        return cleaned if truncated else f'"{bare}"'
    if provider in {"openalex", "scielo", "bvs_lilacs"}:
        if provider != "openalex" and truncated:
            return cleaned[:-1] + "$"
        word = cleaned.rstrip("*")
        return f'"{word}"' if " " in word else word
    return bare


def _block_terms(block: Mapping[str, Any], provider: str, include_pt: bool) -> list[str]:
    regional = provider in LINK_PROVIDERS
    selected: list[str] = []
    for term in block["terms"]:
        if term.get("enabled") is False:
            continue
        lang = term.get("lang")
        if lang == "pt" and not (regional or include_pt):
            continue
        selected.append(term["text"])
    if regional:
        pt_first = [t["text"] for t in block["terms"] if t.get("lang") == "pt" and t.get("enabled") is not False]
        others = [text for text in selected if text not in pt_first]
        selected = pt_first + others
    return selected


def _compile_boolean(blocks: list[Mapping[str, Any]], provider: str, field_mode: str, include_pt: bool) -> str:
    parts: list[str] = []
    for block in blocks:
        formatted: list[str] = []
        for text in _block_terms(block, provider, include_pt):
            item = _format_term(text, provider, field_mode)
            if item and item not in formatted:
                formatted.append(item)
        if provider == "pubmed":
            for item in block.get("pubmed_filters") or []:
                if item not in formatted:
                    formatted.append(item)
        if formatted:
            # BVS only reads a parenthesised group inside a field: tw:(a OR b). A bare
            # group falls back to the whole collection (verified on the live portal).
            prefix = "tw:" if provider == "bvs_lilacs" else ""
            parts.append(prefix + "(" + " OR ".join(formatted) + ")")
    return " AND ".join(parts)


def _crossref_keywords(blocks: list[Mapping[str, Any]]) -> str:
    """Crossref has no Boolean search: the first two non-Portuguese terms of each
    block plus the synonyms the person added, capped at MAX_CROSSREF_WORDS words."""

    words: list[str] = []
    for block in blocks:
        usable = [t for t in block["terms"] if t.get("lang") != "pt" and t.get("enabled") is not False]
        picked = [t["text"] for t in usable[:2]] + [t["text"] for t in usable[2:] if t.get("added")]
        for text in picked:
            for word in _clean(text).rstrip("*").split(" "):
                word = word.rstrip("*")
                if word and word.casefold() not in {w.casefold() for w in words}:
                    words.append(word)
    return " ".join(words[:MAX_CROSSREF_WORDS])


def _year_bounds(plan: Mapping[str, Any]) -> tuple[int | None, int | None]:
    return plan.get("year_from"), plan.get("year_to")


def compile_queries(
    plan: Mapping[str, Any],
    *,
    field_mode: str = "title_abstract",
    include_pt: bool = False,
    current_year: int,
) -> dict[str, Any]:
    """Compile one query per source from an (optionally edited) plan."""

    if field_mode not in FIELD_MODES:
        raise ValueError(f"field_mode must be one of {FIELD_MODES}")
    year_from, year_to = _year_bounds(plan)
    enabled = [block for block in plan.get("blocks") or [] if block.get("enabled")]
    manual = plan.get("mode") == "manual"
    providers: dict[str, dict[str, Any]] = {}

    def boolean(provider: str) -> str:
        return str(plan.get("question") or "") if manual else _compile_boolean(enabled, provider, field_mode, include_pt)

    pubmed = boolean("pubmed")
    if pubmed and not manual and (year_from or year_to):
        pubmed += f" AND ({year_from or 1800}:{year_to or 3000}[dp])"
    providers["pubmed"] = {
        "query": pubmed,
        "params": {"sort": "relevance"},
        "dialect": "pubmed_manual" if manual else f"pubmed_{field_mode}",
        "site_url": "https://pubmed.ncbi.nlm.nih.gov/?" + _query_string({"term": pubmed}) if pubmed else "",
        "notes": ["pubmed_automatic_term_mapping"] if field_mode == "broad" and not manual else [],
    }

    europepmc = boolean("europepmc")
    if europepmc and not manual and (year_from or year_to):
        europepmc += f" AND (PUB_YEAR:[{year_from or 1800} TO {year_to or current_year + 1}])"
    epmc_params = {"synonym": "true"} if field_mode == "broad" and not manual else {}
    providers["europepmc"] = {
        "query": europepmc,
        "params": epmc_params,
        "dialect": "europepmc_manual" if manual else f"europepmc_{field_mode}",
        "site_url": "https://europepmc.org/search?" + _query_string({"query": europepmc}) if europepmc else "",
        "notes": ["europepmc_synonyms"] if epmc_params else [],
    }

    openalex = boolean("openalex")
    openalex_filters = []
    if year_from:
        openalex_filters.append(f"from_publication_date:{year_from}-01-01")
    if year_to:
        openalex_filters.append(f"to_publication_date:{year_to}-12-31")
    openalex_params = {"filter": ",".join(openalex_filters)} if openalex_filters else {}
    providers["openalex"] = {
        "query": openalex,
        "params": openalex_params,
        "dialect": "openalex_manual" if manual else "openalex_search_boolean",
        "site_url": "https://api.openalex.org/works?" + _query_string({"search": openalex, **openalex_params}) if openalex else "",
        "notes": ["openalex_no_truncation_fulltext"],
    }

    crossref = str(plan.get("question") or "") if manual else _crossref_keywords(enabled)
    crossref_filters = []
    if year_from:
        crossref_filters.append(f"from-pub-date:{year_from}")
    if year_to:
        crossref_filters.append(f"until-pub-date:{year_to}")
    crossref_params = {"filter": ",".join(crossref_filters)} if crossref_filters else {}
    providers["crossref"] = {
        "query": crossref,
        "params": crossref_params,
        "dialect": "crossref_manual" if manual else "crossref_relevance_keywords",
        "site_url": "https://api.crossref.org/works?" + _query_string({"query.bibliographic": crossref, **crossref_params}) if crossref else "",
        "notes": ["crossref_no_boolean"],
    }

    bvs = boolean("bvs_lilacs")
    providers["bvs_lilacs"] = {
        "query": bvs,
        "params": {},
        "dialect": "bvs_manual" if manual else "bvs_tw_block_pt_en",
        "site_url": "https://pesquisa.bvsalud.org/portal/?" + _query_string({"lang": "pt", "q": bvs, "filter[db_cluster][]": "LILACS"}) if bvs else "",
        "notes": ["link_only", "years_on_site"] if (year_from or year_to) else ["link_only"],
    }

    scielo = boolean("scielo")
    providers["scielo"] = {
        "query": scielo,
        "params": {},
        "dialect": "scielo_manual" if manual else "scielo_boolean_pt_en",
        "site_url": "https://search.scielo.org/?" + _query_string({"lang": "pt", "q": scielo}) if scielo else "",
        "notes": ["link_only", "years_on_site"] if (year_from or year_to) else ["link_only"],
    }

    return {
        "field_mode": field_mode,
        "include_pt": include_pt,
        "manual": manual,
        "logic": " AND ".join(
            "(" + block["label_en"] + ")" for block in enabled
        ),
        "providers": providers,
    }


def to_review_strategy(plan: Mapping[str, Any], framework: str = "PICO") -> dict[str, Any] | None:
    """Project enabled blocks into the hosted structured-review strategy schema."""

    concepts = []
    for block in plan.get("blocks") or []:
        if not block.get("enabled"):
            continue
        terms = [f"free:{t['text']}" for t in block["terms"] if t.get("lang") != "pt" and t.get("enabled") is not False]
        if not terms:
            continue
        concepts.append({"label": block["label_en"][:80], "terms": terms[:80]})
    if not concepts:
        return None
    return {"framework": framework, "concepts": concepts[:8]}
