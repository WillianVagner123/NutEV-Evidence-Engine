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


# Country-name -> ISO alpha-2 lookup used to recover geography from free-text
# affiliation strings (PubMed/Crossref carry no structured country code). Covers
# every country present in ``_REGION_GROUPS`` plus the common short forms,
# adjectives and historical/colloquial variants seen in affiliation lines.
# Keys are lowercase; matching is word-boundary and longest-name-first so that
# e.g. "united states" wins over "states" and "nigeria" over "niger".
_COUNTRY_NAMES: dict[str, str] = {
    # --- Africa ---
    "algeria": "DZ",
    "angola": "AO",
    "benin": "BJ",
    "botswana": "BW",
    "burkina faso": "BF",
    "burundi": "BI",
    "cape verde": "CV",
    "cabo verde": "CV",
    "cameroon": "CM",
    "central african republic": "CF",
    "chad": "TD",
    "comoros": "KM",
    "republic of the congo": "CG",
    "congo-brazzaville": "CG",
    "democratic republic of the congo": "CD",
    "dr congo": "CD",
    "congo-kinshasa": "CD",
    "ivory coast": "CI",
    "cote d'ivoire": "CI",
    "côte d'ivoire": "CI",
    "djibouti": "DJ",
    "egypt": "EG",
    "equatorial guinea": "GQ",
    "eritrea": "ER",
    "eswatini": "SZ",
    "swaziland": "SZ",
    "ethiopia": "ET",
    "gabon": "GA",
    "gambia": "GM",
    "ghana": "GH",
    "guinea-bissau": "GW",
    "guinea bissau": "GW",
    "guinea": "GN",
    "kenya": "KE",
    "lesotho": "LS",
    "liberia": "LR",
    "libya": "LY",
    "madagascar": "MG",
    "malawi": "MW",
    "mali": "ML",
    "mauritania": "MR",
    "mauritius": "MU",
    "morocco": "MA",
    "mozambique": "MZ",
    "namibia": "NA",
    "nigeria": "NG",
    "niger": "NE",
    "rwanda": "RW",
    "sao tome and principe": "ST",
    "são tomé and príncipe": "ST",
    "senegal": "SN",
    "seychelles": "SC",
    "sierra leone": "SL",
    "somalia": "SO",
    "south africa": "ZA",
    "south sudan": "SS",
    "sudan": "SD",
    "tanzania": "TZ",
    "togo": "TG",
    "tunisia": "TN",
    "uganda": "UG",
    "western sahara": "EH",
    "zambia": "ZM",
    "zimbabwe": "ZW",
    # --- Asia ---
    "afghanistan": "AF",
    "armenia": "AM",
    "azerbaijan": "AZ",
    "bahrain": "BH",
    "bangladesh": "BD",
    "bhutan": "BT",
    "brunei": "BN",
    "cambodia": "KH",
    "china": "CN",
    "people's republic of china": "CN",
    "pr china": "CN",
    "p.r. china": "CN",
    "mainland china": "CN",
    "cyprus": "CY",
    "georgia": "GE",
    "hong kong": "HK",
    "india": "IN",
    "indonesia": "ID",
    "iran": "IR",
    "islamic republic of iran": "IR",
    "iraq": "IQ",
    "israel": "IL",
    "japan": "JP",
    "jordan": "JO",
    "kazakhstan": "KZ",
    "kuwait": "KW",
    "kyrgyzstan": "KG",
    "laos": "LA",
    "lebanon": "LB",
    "macao": "MO",
    "macau": "MO",
    "malaysia": "MY",
    "maldives": "MV",
    "mongolia": "MN",
    "myanmar": "MM",
    "burma": "MM",
    "nepal": "NP",
    "north korea": "KP",
    "oman": "OM",
    "pakistan": "PK",
    "palestine": "PS",
    "philippines": "PH",
    "qatar": "QA",
    "saudi arabia": "SA",
    "singapore": "SG",
    "south korea": "KR",
    "republic of korea": "KR",
    "korea": "KR",
    "sri lanka": "LK",
    "syria": "SY",
    "taiwan": "TW",
    "tajikistan": "TJ",
    "thailand": "TH",
    "timor-leste": "TL",
    "east timor": "TL",
    "turkey": "TR",
    "turkiye": "TR",
    "türkiye": "TR",
    "turkmenistan": "TM",
    "united arab emirates": "AE",
    "uae": "AE",
    "uzbekistan": "UZ",
    "vietnam": "VN",
    "viet nam": "VN",
    "yemen": "YE",
    # --- Europe ---
    "albania": "AL",
    "andorra": "AD",
    "austria": "AT",
    "belarus": "BY",
    "belgium": "BE",
    "bosnia and herzegovina": "BA",
    "bosnia": "BA",
    "bulgaria": "BG",
    "croatia": "HR",
    "czech republic": "CZ",
    "czechia": "CZ",
    "denmark": "DK",
    "estonia": "EE",
    "finland": "FI",
    "france": "FR",
    "germany": "DE",
    "greece": "GR",
    "hungary": "HU",
    "iceland": "IS",
    "ireland": "IE",
    "italy": "IT",
    "kosovo": "XK",
    "latvia": "LV",
    "liechtenstein": "LI",
    "lithuania": "LT",
    "luxembourg": "LU",
    "malta": "MT",
    "moldova": "MD",
    "monaco": "MC",
    "montenegro": "ME",
    "the netherlands": "NL",
    "netherlands": "NL",
    "holland": "NL",
    "north macedonia": "MK",
    "macedonia": "MK",
    "norway": "NO",
    "poland": "PL",
    "portugal": "PT",
    "romania": "RO",
    "russian federation": "RU",
    "russia": "RU",
    "san marino": "SM",
    "serbia": "RS",
    "slovakia": "SK",
    "slovenia": "SI",
    "spain": "ES",
    "sweden": "SE",
    "switzerland": "CH",
    "ukraine": "UA",
    "united kingdom": "GB",
    "united kingdom of great britain and northern ireland": "GB",
    "great britain": "GB",
    "uk": "GB",
    "u.k.": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",
    "vatican city": "VA",
    "vatican": "VA",
    # --- North America ---
    "antigua and barbuda": "AG",
    "bahamas": "BS",
    "barbados": "BB",
    "belize": "BZ",
    "canada": "CA",
    "costa rica": "CR",
    "cuba": "CU",
    "dominica": "DM",
    "dominican republic": "DO",
    "el salvador": "SV",
    "grenada": "GD",
    "guatemala": "GT",
    "haiti": "HT",
    "honduras": "HN",
    "jamaica": "JM",
    "mexico": "MX",
    "méxico": "MX",
    "nicaragua": "NI",
    "panama": "PA",
    "saint kitts and nevis": "KN",
    "saint lucia": "LC",
    "saint vincent and the grenadines": "VC",
    "trinidad and tobago": "TT",
    "united states of america": "US",
    "united states": "US",
    "u.s.a.": "US",
    "u.s.": "US",
    "usa": "US",
    "puerto rico": "PR",
    # --- South America ---
    "argentina": "AR",
    "bolivia": "BO",
    "brazil": "BR",
    "brasil": "BR",
    "chile": "CL",
    "colombia": "CO",
    "ecuador": "EC",
    "guyana": "GY",
    "paraguay": "PY",
    "peru": "PE",
    "perú": "PE",
    "suriname": "SR",
    "uruguay": "UY",
    "venezuela": "VE",
    # --- Oceania ---
    "australia": "AU",
    "fiji": "FJ",
    "kiribati": "KI",
    "marshall islands": "MH",
    "micronesia": "FM",
    "nauru": "NR",
    "new zealand": "NZ",
    "palau": "PW",
    "papua new guinea": "PG",
    "samoa": "WS",
    "solomon islands": "SB",
    "tonga": "TO",
    "tuvalu": "TV",
    "vanuatu": "VU",
}

# Pre-compile one alternation, longest names first so "united states" matches
# before "states" and "nigeria" before "niger". ``re.escape`` keeps the literal
# dots in variants like "u.s.a." from acting as wildcards. Word-character
# boundaries (rather than ``\b``) stop substring collisions such as "oman"
# inside "Romania" or "niger" inside "nigeria" while still allowing a trailing
# period/comma/semicolon after a country name (e.g. "..., Brazil.").
_COUNTRY_NAME_RE = re.compile(
    r"(?<!\w)(?:"
    + "|".join(re.escape(name) for name in sorted(_COUNTRY_NAMES, key=len, reverse=True))
    + r")(?!\w)",
    re.IGNORECASE,
)


def country_from_text(text: str) -> list[str]:
    """Recover ISO alpha-2 country codes from a free-text affiliation string.

    Scans ``text`` for any known country name / common variant and returns the
    de-duplicated alpha-2 codes in order of first appearance. Returns ``[]`` for
    empty or ``None`` input. Matching is case-insensitive, word-boundary aware
    and longest-name-first to avoid substring collisions.
    """
    if not text:
        return []
    out: list[str] = []
    for match in _COUNTRY_NAME_RE.finditer(text):
        code = _COUNTRY_NAMES.get(match.group(0).lower())
        if code and code not in out:
            out.append(code)
    return out


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
    # OpenAlex country_codes are the primary signal; when absent (PubMed/Crossref
    # and other free-text providers) recover countries from affiliation strings.
    if not countries:
        affiliation_text = " ; ".join(
            _as_list(row.get("affiliations")) + _as_list(row.get("affiliation"))
        )
        for code in country_from_text(affiliation_text):
            if code not in countries:
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
