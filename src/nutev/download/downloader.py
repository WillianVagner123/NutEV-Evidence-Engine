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

SESSION_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
}


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
            response.raise_for_status()
            return response
        except Exception as exc:
            last_error = exc
            time.sleep(0.8 * attempt)
    raise RuntimeError(f"download failed after retries: {last_error}")


def _host_matches(url: str, hints: set[str]) -> bool:
    host = urlparse(url).netloc.lower()
    return any(hint in host for hint in hints)


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
    if not _looks_html_candidate(candidate_url, record.get("source")):
        return None

    try:
        logger.info("snapshot tentativa url=%s", candidate_url)
        response = session.get(candidate_url, timeout=25, allow_redirects=True)
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
    candidates: list[str] = []
    doi_url = _candidate_doi_url(record)
    if doi_url:
        candidates.append(doi_url)
    candidates.extend(_derive_landing_from_url(resolved_url))
    candidates.extend(_derive_landing_from_url(raw_url))
    candidates.append(resolved_url)
    if raw_url != resolved_url:
        candidates.append(raw_url)

    seen_candidates: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen_candidates:
            continue
        seen_candidates.add(candidate)
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

        resolved_url, resolved_kind = resolve_url(raw_url)
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
                logger.info("download falhou url=%s erro=%s", resolved_url, exc)
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
                    {
                        "url": raw_url,
                        "resolved_url": resolved_url,
                        "status": "fail",
                        "reason": str(exc),
                        "head_status": head_status,
                    }
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

        failed.append(
            {
                "url": raw_url,
                "resolved_url": resolved_url,
                "status": "filtered_no_snapshot",
                "reason": "filtered_and_no_html_snapshot",
                "head_status": head_status,
            }
        )

    return manifest, failed
