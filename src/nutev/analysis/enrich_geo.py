"""Geographic, venue and language enrichment for the article knowledge base.

Populates the (previously empty) ``country`` / ``region`` / ``language`` /
``source_institution`` columns plus venue identity, so the corpus can answer
"what is each country publishing", "where is it published" and "in which
language". The richest signal comes from OpenAlex (author-institution country
codes, work language, ISSN/publisher); other providers contribute what they
carry. Language falls back to a lightweight script/stopword detector.
"""

from __future__ import annotations

import re

# Continent/region per ISO-3166 alpha-2 country code. Region granularity is
# continent-level, which is the most robust grouping for cross-country analysis.
_REGION_GROUPS: dict[str, list[str]] = {
    "Africa": [
        "DZ", "AO", "BJ", "BW", "BF", "BI", "CV", "CM", "CF", "TD", "KM", "CG", "CD", "CI", "DJ",
        "EG", "GQ", "ER", "SZ", "ET", "GA", "GM", "GH", "GN", "GW", "KE", "LS", "LR", "LY", "MG",
        "MW", "ML", "MR", "MU", "MA", "MZ", "NA", "NE", "NG", "RW", "ST", "SN", "SC", "SL", "SO",
        "ZA", "SS", "SD", "TZ", "TG", "TN", "UG", "EH", "ZM", "ZW",
    ],
    "Asia": [
        "AF", "AM", "AZ", "BH", "BD", "BT", "BN", "KH", "CN", "CY", "GE", "HK", "IN", "ID", "IR",
        "IQ", "IL", "JP", "JO", "KZ", "KW", "KG", "LA", "LB", "MO", "MY", "MV", "MN", "MM", "NP",
        "KP", "OM", "PK", "PS", "PH", "QA", "SA", "SG", "KR", "LK", "SY", "TW", "TJ", "TH", "TL",
        "TR", "TM", "AE", "UZ", "VN", "YE",
    ],
    "Europe": [
        "AL", "AD", "AT", "BY", "BE", "BA", "BG", "HR", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
        "HU", "IS", "IE", "IT", "XK", "LV", "LI", "LT", "LU", "MT", "MD", "MC", "ME", "NL", "MK",
        "NO", "PL", "PT", "RO", "RU", "SM", "RS", "SK", "SI", "ES", "SE", "CH", "UA", "GB", "VA",
    ],
    "North America": [
        "AG", "BS", "BB", "BZ", "CA", "CR", "CU", "DM", "DO", "SV", "GD", "GT", "HT", "HN", "JM",
        "MX", "NI", "PA", "KN", "LC", "VC", "TT", "US", "PR",
    ],
    "South America": [
        "AR", "BO", "BR", "CL", "CO", "EC", "GY", "PY", "PE", "SR", "UY", "VE",
    ],
    "Oceania": [
        "AU", "FJ", "KI", "MH", "FM", "NR", "NZ", "PW", "PG", "WS", "SB", "TO", "TV", "VU",
    ],
}

_REGION_BY_COUNTRY: dict[str, str] = {code: region for region, codes in _REGION_GROUPS.items() for code in codes}


def region_for(country_code: str) -> str:
    return _REGION_BY_COUNTRY.get((country_code or "").strip().upper(), "")


# Unicode-script ranges for the non-Latin languages we actively search for.
# Kana is checked before Han so Japanese is not misread as Chinese.
_SCRIPT_PATTERNS: list[tuple[str, str]] = [
    ("ja", "[぀-ヿ]"),   # hiragana/katakana -> Japanese
    ("ko", "[가-힯]"),   # Hangul
    ("zh", "[一-鿿]"),   # Han -> Chinese
    ("ru", "[Ѐ-ӿ]"),   # Cyrillic
    ("ar", "[؀-ۿ]"),   # Arabic
    ("el", "[Ͱ-Ͽ]"),   # Greek
    ("he", "[֐-׿]"),   # Hebrew
    ("hi", "[ऀ-ॿ]"),   # Devanagari
    ("th", "[฀-๿]"),   # Thai
]

# Distinctive stopwords for the Latin-script languages we expand into.
_LATIN_STOPWORDS: dict[str, set[str]] = {
    "pt": {"e", "de", "da", "do", "uma", "para", "com", "não", "saúde", "estudo", "doença"},
    "es": {"y", "de", "la", "el", "una", "para", "con", "salud", "estudio", "enfermedad"},
    "fr": {"et", "de", "la", "le", "une", "pour", "avec", "santé", "étude", "maladie"},
    "de": {"und", "der", "die", "das", "mit", "für", "eine", "gesundheit", "studie", "krankheit"},
    "it": {"e", "di", "la", "il", "una", "per", "con", "salute", "studio", "malattia"},
}

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def detect_language(text: str) -> str:
    """Best-effort language code from script ranges, then Latin stopwords.

    Returns an ISO-639-1 code or "" when undetermined. Used only as a fallback
    when the provider does not report a language.
    """
    if not text:
        return ""
    for code, pattern in _SCRIPT_PATTERNS:
        if re.search(pattern, text):
            return code
    tokens = {t.lower() for t in _WORD_RE.findall(text)}
    if not tokens:
        return ""
    best_lang, best_hits = "", 0
    for lang, stops in _LATIN_STOPWORDS.items():
        hits = len(tokens & stops)
        if hits > best_hits:
            best_lang, best_hits = lang, hits
    if best_hits >= 2:
        return best_lang
    return "en"


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [p.strip() for p in re.split(r"[;,]", value) if p.strip()]
    return []


def enrich_record(row: dict) -> dict:
    """Populate canonical geo/venue/language fields on a single record (in place)."""
    codes = [c.upper() for c in _as_list(row.get("country_codes"))]
    # de-dup preserving order
    countries: list[str] = []
    for code in codes:
        if code and code not in countries:
            countries.append(code)
    row["countries"] = countries
    row["country"] = countries[0] if countries else (row.get("country") or "")
    row["region"] = next((region_for(c) for c in countries if region_for(c)), row.get("region") or "")

    language = (row.get("language") or "").strip()
    if not language:
        language = detect_language(f"{row.get('title', '')} {row.get('abstract', '')}".strip())
    row["language"] = language

    row["source_institution"] = row.get("source_institution") or ""
    row["issn"] = row.get("issn") or ""
    row["publisher"] = row.get("publisher") or ""
    try:
        row["cited_by_count"] = int(row.get("cited_by_count") or 0)
    except (TypeError, ValueError):
        row["cited_by_count"] = 0
    return row


def enrich_records(rows: list[dict]) -> list[dict]:
    return [enrich_record(r) for r in rows]
