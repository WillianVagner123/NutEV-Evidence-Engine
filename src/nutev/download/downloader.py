from __future__ import annotations

import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from nutev.download.dedup import Deduplicator
from nutev.download.filters import is_likely_relevant_url, should_download
from nutev.download.naming import build_filename, infer_ext
from nutev.download.resolver import extract_clean_doi, resolve_url

SCHOLARLY_HTML_HOSTS = {
    "springer.com",
    "nature.com",
    "cambridge.org",
    "frontiersin.org",
    "karger.com",
    "oup.com",
    "ahajournals.org",
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "scielo.br",
    "cureus.com",
    "dovepress.com",
    "diabetesjournals.org",
    "lifestylemedicine.org",
    "who.int",
    "heart.org",
    "abccardiol.org",
    "bmj.com",
    "biomedcentral.com",
    "taylorfrancis.com",
}

BLOCKED_PUBLISHER_HINTS = {
    "academic.oup.com",
    "ahajournals.org",
    "doi.apa.org",
    "journals.sagepub.com",
    "karger.com",
    "linkinghub.elsevier.com",
    "mayoclinicproceedings.org",
    "mdpi.com",
    "onlinelibrary.wiley.com",
    "scielo.br",
    "tandfonline.com",
}

HIGH_FRICTION_HOST_REASONS = {
    "academic.oup.com": "blocked_oup",
    "bmjopen.bmj.com": "blocked_bmj",
    "diabetesjournals.org": "blocked_diabetesjournals",
    "dom-pubs.pericles-prod.literatumonline.com": "blocked_wiley_literatum",
    "journals.lww.com": "blocked_lww",
    "journalslibrary.nihr.ac.uk": "method_not_allowed_nihr",
    "mdpi.com": "blocked_mdpi",
    "nejm.org": "blocked_nejm",
    "onlinelibrary.wiley.com": "blocked_wiley",
    "pubmed.ncbi.nlm.nih.gov": "pubmed_metadata_page",
    "scielo.br": "blocked_scielo",
    "webofscience.com": "metadata_index_only",
}

DOI_PREFIX_REASONS = {
    "10.1056": "blocked_nejm",
    "10.1093": "blocked_oup",
    "10.1097": "blocked_lww",
    "10.1111": "blocked_wiley",
    "10.1136": "blocked_bmj",
    "10.2337": "blocked_diabetesjournals",
    "10.3390": "blocked_mdpi",
    "10.36660": "blocked_scielo",
}

SESSION_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.8,*/*;q=0.7",
}


class ControlledDownloadFailure(RuntimeError):
    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


def _head(url: str, timeout: int = 15) -> tuple[int, str]:
    try:
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=SESSION_HEADERS,
        )
        return response.status_code, response.headers.get("Content-Type", "")
    except Exception:
        return 0, ""


def _host(url: str) -> str:
    return urlparse(url or "").netloc.lower()


def _host_matches(url: str, hints: set[str]) -> bool:
    host = _host(url)
    return any(hint in host for hint in hints)


def _is_blocked_publisher(url: str) -> bool:
    return _host_matches(url, BLOCKED_PUBLISHER_HINTS)


def _host_policy_reason(url: str) -> str | None:
    host = _host(url)
    for hint, reason in HIGH_FRICTION_HOST_REASONS.items():
        if hint in host:
            return reason
    return None


def _doi_policy_reason(value: str | None) -> str | None:
    doi = extract_clean_doi(value)
    if not doi:
        return None
    doi_lower = doi.lower()
    for prefix, reason in DOI_PREFIX_REASONS.items():
        if doi_lower.startswith(prefix):
            return reason
    return None


def _capture_policy_key(url: str) -> str | None:
    doi_reason = _doi_policy_reason(url)
    if doi_reason:
        return f"doi:{doi_reason}"
    host_reason = _host_policy_reason(url)
    if host_reason:
        return f"host:{host_reason}"
    return None


def _is_pubmed_landing(url: str) -> bool:
    return "pubmed.ncbi.nlm.nih.gov" in _host(url)


def _metadata_only(
    raw_url: str,
    resolved_url: str,
    reason: str,
    head_status: int = 0,
) -> dict:
    return {
        "url": raw_url,
        "resolved_url": resolved_url,
        "status": "metadata_only",
        "reason": reason,
        "head_status": head_status,
    }


def _failure_reason(exc: Exception, url: str, head_status: int = 0) -> str:
    if isinstance(exc, ControlledDownloadFailure):
        return exc.reason
    status = getattr(getattr(exc, "response", None), "status_code", None) or head_status
    policy_reason = _doi_policy_reason(url) or _host_policy_reason(url)
    if status in {401, 403}:
        return policy_reason or "publisher_forbidden"
    if status == 400:
        return "bad_source_url"
    if status == 404:
        return "not_found"
    if status == 405:
        return policy_reason or "method_not_allowed"
    if status == 429:
        return "rate_limited"
    if status and status >= 500:
        return "server_error"
    if policy_reason:
        return policy_reason
    if _is_blocked_publisher(url):
        return "publisher_blocked_or_paywalled"
    return "download_failed"


def _request_with_retry(
    session: requests.Session,
    url: str,
    logger,
    retries: int = 2,
):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            logger.info("download tentativa=%d url=%s", attempt, url)
            response = session.get(url, timeout=25, allow_redirects=True)
            if response.status_code in {400, 401, 403, 404, 405, 429}:
                reason = _failure_reason(requests.HTTPError(response=response), response.url)
                raise ControlledDownloadFailure(
                    reason,
                    f"controlled download stop: {response.status_code} for {response.url}",
                )
            response.raise_for_status()
            return response
        except ControlledDownloadFailure:
            raise
        except requests.HTTPError as exc:
            last_error = exc
            status = getattr(exc.response, "status_code", 0)
            if status in {400, 401, 403, 404, 405, 429} or _is_blocked_publisher(url):
                break
            time.sleep(0.8 * attempt)
        except Exception as exc:
            last_error = exc
            if _is_blocked_publisher(url) or _host_policy_reason(url):
                break
            time.sleep(0.8 * attempt)
    raise RuntimeError(f"download failed after retries: {last_error}")


def _looks_html_candidate(url: str, source: str | None = None) -> bool:
    normalized_url = (url or "").lower()
    if not normalized_url.startswith(("http://", "https://")):
        return False
    if source == "official":
        return True
    if _host_matches(url, SCHOLARLY_HTML_HOSTS):
        return True
    return any(
        token in normalized_url
        for token in [
            "/article",
            "/articles",
            "/doi",
            "/content",
            "/journal",
            "/journals",
            "guideline",
            "statement",
            "consensus",
            "framework",
            "questionnaire",
            "recommendation",
        ]
    )


def _looks_like_pdf_bytes(content: bytes) -> bool:
    return content[:8].startswith(b"%PDF-")


def _looks_like_html_bytes(content: bytes) -> bool:
    header = content[:4096].lower()
    return (
        b"<html" in header
        or b"<!doctype html" in header
        or b"<body" in header
    )


def _candidate_doi_url(record: dict) -> str | None:
    doi = extract_clean_doi(record.get("doi"))
    if doi and record.get("source") != "official":
        return f"https://doi.org/{doi}"
    return None


def _primary_download_url(record: dict, raw_url: str) -> str | None:
    if _is_pubmed_landing(raw_url):
        return _candidate_doi_url(record)
    return raw_url


def _derive_landing_from_url(url: str) -> list[str]:
    derived_urls: list[str] = []
    if not url:
        return derived_urls

    if "onlinelibrary.wiley.com/doi/pdfdirect/" in url:
        derived_urls.append(url.replace("/doi/pdfdirect/", "/doi/"))
    if "onlinelibrary.wiley.com/doi/pdf/" in url:
        derived_urls.append(url.replace("/doi/pdf/", "/doi/"))
    if "ahajournals.org/doi/pdf/" in url:
        derived_urls.append(url.replace("/doi/pdf/", "/doi/"))
    if "bmj.com/content/" in url and url.endswith(".full.pdf"):
        derived_urls.append(url[:-9])
    if "/article-pdf/" in url and url.lower().endswith(".pdf"):
        article_url = url.replace("/article-pdf/", "/article/")
        parts = article_url.split("/")
        if parts[-1].lower().endswith(".pdf") and len(parts) > 1:
            derived_urls.append("/".join(parts[:-1]))
    return derived_urls


def _save_snapshot_html(
    session: requests.Session,
    candidate_url: str,
    record: dict,
    public_dir: Path,
    official_dir: Path,
    dedup: Deduplicator,
    logger,
) -> dict | None:
    if not candidate_url or not is_likely_relevant_url(candidate_url):
        return None
    if _is_pubmed_landing(candidate_url):
        return None
    if not _looks_html_candidate(candidate_url, record.get("source")):
        return None

    try:
        logger.info("snapshot tentativa url=%s", candidate_url)
        response = session.get(candidate_url, timeout=25, allow_redirects=True)
        if response.status_code in {400, 401, 403, 404, 405, 429}:
            logger.info(
                "snapshot bloqueado url=%s status=%s reason=%s",
                response.url,
                response.status_code,
                _failure_reason(requests.HTTPError(response=response), response.url),
            )
            return None
        response.raise_for_status()
    except Exception as exc:
        logger.info("snapshot falhou url=%s erro=%s", candidate_url, exc)
        return None

    final_url = response.url
    content_type = (response.headers.get("Content-Type", "") or "").lower()
    content = response.content

    if "html" not in content_type and not _looks_like_html_bytes(content):
        return None
    if dedup.seen_content(content):
        return None

    root = official_dir if record.get("source") == "official" else public_dir
    output_path = root / build_filename(
        record.get("workstream", "na"),
        record.get("source", "src"),
        record.get("title", "doc"),
        final_url,
        "html",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(content)

    logger.info("snapshot html salvo=%s", output_path)

    return {
        "url": record.get("url", ""),
        "resolved_url": final_url,
        "path": str(output_path),
        "ext": "html",
        "source": record.get("source", ""),
        "status": "ok_html_snapshot",
    }


def _snapshot_candidates(
    record: dict,
    raw_url: str,
    resolved_url: str,
) -> list[str]:
    candidates: list[str] = []
    doi_url = _candidate_doi_url(record)
    if doi_url:
        candidates.append(doi_url)
    candidates.extend(_derive_landing_from_url(resolved_url))
    candidates.extend(_derive_landing_from_url(raw_url))
    candidates.append(resolved_url)
    if raw_url != resolved_url:
        candidates.append(raw_url)
    return candidates


def _try_snapshot_fallbacks(
    session: requests.Session,
    record: dict,
    raw_url: str,
    resolved_url: str,
    public_dir: Path,
    official_dir: Path,
    dedup: Deduplicator,
    logger,
) -> dict | None:
    seen_candidates: set[str] = set()
    seen_policy_keys: set[str] = set()
    for candidate in _snapshot_candidates(record, raw_url, resolved_url):
        if not candidate or candidate in seen_candidates:
            continue
        seen_candidates.add(candidate)

        policy_key = _capture_policy_key(candidate)
        if policy_key and policy_key in seen_policy_keys:
            continue
        if policy_key:
            seen_policy_keys.add(policy_key)

        snapshot = _save_snapshot_html(
            session,
            candidate,
            record,
            public_dir,
            official_dir,
            dedup,
            logger,
        )
        if snapshot:
            return snapshot
    return None


def download_records(
    records: list[dict],
    public_dir: Path,
    official_dir: Path,
    logger,
) -> tuple[list[dict], list[dict]]:
    dedup = Deduplicator()
    manifest: list[dict] = []
    failed: list[dict] = []
    session = requests.Session()
    session.headers.update(SESSION_HEADERS)

    for record in records:
        raw_url = record.get("url")
        if not isinstance(raw_url, str) or not raw_url:
            continue
        if dedup.seen_url(raw_url):
            continue

        primary_url = _primary_download_url(record, raw_url)
        if not primary_url:
            failed.append(
                _metadata_only(
                    raw_url,
                    raw_url,
                    "pubmed_no_doi_or_pmc_target",
                )
            )
            continue

        resolved_url, resolved_kind = resolve_url(primary_url)
        head_status, content_type = _head(resolved_url)
        ext = infer_ext(resolved_url, content_type)

        if resolved_kind == "pdf" and ext == "bin":
            ext = "pdf"
        if resolved_kind == "html" and ext == "bin":
            ext = "html"

        if should_download(resolved_url, ext, record.get("source")):
            root = (
                official_dir if record.get("source") == "official" else public_dir
            )

            try:
                response = _request_with_retry(session, resolved_url, logger)
                final_url = response.url
                final_content_type = (
                    response.headers.get("Content-Type", "") or ""
                ).lower()
                content = response.content

                final_ext = ext
                if final_ext == "pdf" and not _looks_like_pdf_bytes(content):
                    if "html" in final_content_type or _looks_like_html_bytes(
                        content
                    ):
                        final_ext = "html"
                    else:
                        final_ext = "bin"

                if (
                    final_ext in {"html", "htm"}
                    and not _looks_like_html_bytes(content)
                    and "html" not in final_content_type
                ):
                    snapshot = _try_snapshot_fallbacks(
                        session,
                        record,
                        raw_url,
                        resolved_url,
                        public_dir,
                        official_dir,
                        dedup,
                        logger,
                    )
                    if snapshot:
                        manifest.append(snapshot)
                        continue

                if dedup.seen_content(content):
                    continue

                output_path = root / build_filename(
                    record.get("workstream", "na"),
                    record.get("source", "src"),
                    record.get("title", "doc"),
                    final_url,
                    final_ext,
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(content)

                logger.info("download ok path=%s", output_path)

                manifest.append(
                    {
                        "url": raw_url,
                        "resolved_url": final_url,
                        "path": str(output_path),
                        "ext": final_ext,
                        "source": record.get("source", ""),
                        "status": "ok",
                    }
                )
                continue

            except Exception as exc:
                reason = _failure_reason(exc, resolved_url, head_status)
                logger.info("download falhou url=%s reason=%s erro=%s", resolved_url, reason, exc)
                snapshot = _try_snapshot_fallbacks(
                    session,
                    record,
                    raw_url,
                    resolved_url,
                    public_dir,
                    official_dir,
                    dedup,
                    logger,
                )
                if snapshot:
                    manifest.append(snapshot)
                    continue

                failed.append(
                    _metadata_only(
                        raw_url,
                        resolved_url,
                        reason,
                        head_status,
                    )
                )
                continue

        logger.info("URLs filtradas: %s", resolved_url)
        snapshot = _try_snapshot_fallbacks(
            session,
            record,
            raw_url,
            resolved_url,
            public_dir,
            official_dir,
            dedup,
            logger,
        )
        if snapshot:
            manifest.append(snapshot)
            continue

        filtered_reason = _doi_policy_reason(resolved_url) or _host_policy_reason(resolved_url)
        failed.append(
            _metadata_only(
                raw_url,
                resolved_url,
                filtered_reason or "filtered_and_no_html_snapshot",
                head_status,
            )
        )

    return manifest, failed
