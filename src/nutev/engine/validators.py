from __future__ import annotations

import re
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse

from nutev.engine.enums import (
    CaptureStatus,
    DownloadStatus,
    ExtractionStatus,
    FailureReason,
    Workstream,
)

DOI_RE = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.I)
PMID_RE = re.compile(r"^\d{1,12}$")
PMCID_RE = re.compile(r"^PMC\d+$", re.I)
TRACKING_QUERY_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "msclkid",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    raw = unquote(str(doi)).strip()
    raw = raw.replace("DOI:", " ").replace("doi:", " ")
    raw = raw.replace("https://doi.org/", " ").replace("http://doi.org/", " ")
    match = DOI_RE.search(raw)
    if not match:
        return None
    return match.group(1).rstrip(" .;,)").lower()


def normalize_pmid(pmid: str | int | None) -> str | None:
    if pmid is None:
        return None
    value = str(pmid).strip()
    return value if PMID_RE.match(value) else None


def normalize_pmcid(pmcid: str | None) -> str | None:
    if not pmcid:
        return None
    value = str(pmcid).strip().upper()
    if value.startswith("PMC") and PMCID_RE.match(value):
        return value
    if value.isdigit():
        return f"PMC{value}"
    return None


def _normalize_query(query: str) -> str:
    params = [
        (key, value)
        for key, value in parse_qsl(query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_PARAMS
    ]
    return urlencode(params, doseq=True)


def normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    value = str(url).strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    normalized_path = parsed.path.rstrip("/") or parsed.path
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            normalized_path,
            "",
            _normalize_query(parsed.query),
            "",
        )
    )


def canonical_host(url: str | None) -> str:
    parsed = urlparse(url or "")
    return parsed.netloc.lower().removeprefix("www.")


def validate_workstream(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip()
    aliases = {"article3_framework": "artigo3_framework"}
    normalized = aliases.get(normalized, normalized)
    allowed = {item.value for item in Workstream}
    if normalized not in allowed:
        raise ValueError(f"Invalid workstream: {value}")
    return normalized


def validate_enum_value(value: str | None, enum_cls, field_name: str) -> str | None:
    if value in (None, ""):
        return value
    normalized = str(value).strip()
    allowed = {item.value for item in enum_cls}
    if normalized not in allowed:
        raise ValueError(f"Invalid {field_name}: {value}")
    return normalized


def validate_download_status(value: str | None) -> str | None:
    return validate_enum_value(value, DownloadStatus, "download_status")


def validate_capture_status(value: str | None) -> str | None:
    return validate_enum_value(value, CaptureStatus, "capture_status")


def validate_extraction_status(value: str | None) -> str | None:
    return validate_enum_value(value, ExtractionStatus, "extraction_status")


def validate_failure_reason(value: str | None) -> str | None:
    return validate_enum_value(value, FailureReason, "failure_reason")


def canonical_document_key(row: dict) -> str:
    doi = normalize_doi(row.get("doi"))
    if doi:
        return f"doi:{doi}"
    pmid = normalize_pmid(row.get("pmid"))
    if pmid:
        return f"pmid:{pmid}"
    pmcid = normalize_pmcid(row.get("pmcid"))
    if pmcid:
        return f"pmcid:{pmcid}"
    url = normalize_url(row.get("final_url") or row.get("resolved_url") or row.get("url"))
    if url:
        return f"url:{url.lower()}"
    title = str(row.get("title") or "").strip().lower()
    year = str(row.get("year") or "").strip()
    if title:
        return f"title_year:{title}|{year}"
    raise ValueError("Cannot build document key: missing DOI, PMID, PMCID, URL and title")


def assert_status_coherence(row: dict) -> None:
    download_status = row.get("download_status")
    extraction_status = row.get("extraction_status")
    artifact_paths = row.get("artifact_paths") or row.get("file_path") or ""

    if download_status:
        validate_download_status(download_status)
    if row.get("capture_status"):
        validate_capture_status(row.get("capture_status"))
    if extraction_status:
        validate_extraction_status(extraction_status)
    if row.get("failure_reason"):
        validate_failure_reason(row.get("failure_reason"))

    if download_status == DownloadStatus.metadata_only.value and artifact_paths:
        raise ValueError("metadata_only records must not carry downloaded artifact paths")
    if download_status in {DownloadStatus.pdf.value, DownloadStatus.html_snapshot.value} and not artifact_paths:
        raise ValueError(f"{download_status} records must carry artifact_paths/file_path")
    if extraction_status in {
        ExtractionStatus.ok.value,
        ExtractionStatus.ok_native.value,
        ExtractionStatus.ok_native_low_confidence.value,
        ExtractionStatus.ok_ocr.value,
    } and download_status == DownloadStatus.metadata_only.value:
        raise ValueError("metadata_only records cannot have successful extraction status")
