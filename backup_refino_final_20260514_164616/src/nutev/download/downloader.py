from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import time
import requests

from nutev.download.dedup import Deduplicator
from nutev.download.filters import should_download, is_likely_relevant_url
from nutev.download.naming import build_filename, infer_ext
from nutev.download.resolver import resolve_url, extract_clean_doi


SCHOLARLY_HTML_HOSTS = {
    "springer.com", "nature.com", "cambridge.org", "frontiersin.org",
    "karger.com", "oup.com", "ahajournals.org", "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov", "scielo.br", "cureus.com", "dovepress.com",
    "diabetesjournals.org", "lifestylemedicine.org", "who.int", "heart.org",
    "abccardiol.org", "bmj.com", "biomedcentral.com", "taylorfrancis.com"
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
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers=SESSION_HEADERS)
        return r.status_code, r.headers.get("Content-Type", "")
    except Exception:
        return 0, ""


def _request_with_retry(session: requests.Session, url: str, logger, retries: int = 2):
    last = None
    for attempt in range(1, retries + 1):
        try:
            logger.info("download tentativa=%d url=%s", attempt, url)
            r = session.get(url, timeout=25, allow_redirects=True)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            time.sleep(0.8 * attempt)
    raise RuntimeError(f"download failed after retries: {last}")


def _get_with_retry(session: requests.Session, url: str, logger, retries: int = 2) -> bytes:
    r = _request_with_retry(session, url, logger, retries=retries)
    return r.content


def _host_matches(url: str, hints: set[str]) -> bool:
    host = urlparse(url).netloc.lower()
    return any(h in host for h in hints)


def _looks_html_candidate(url: str, source: str | None = None) -> bool:
    u = (url or "").lower()
    if not u.startswith(("http://", "https://")):
        return False
    if source == "official":
        return True
    if _host_matches(url, SCHOLARLY_HTML_HOSTS):
        return True
    return any(tok in u for tok in ["/article", "/articles", "/doi", "/content", "/journal", "/journals", "guideline", "statement", "consensus", "framework", "questionnaire", "recommendation"])


def _looks_like_pdf_bytes(content: bytes) -> bool:
    return content[:8].startswith(b"%PDF-")


def _looks_like_html_bytes(content: bytes) -> bool:
    head = content[:4096].lower()
    return b"<html" in head or b"<!doctype html" in head or b"<body" in head


def _candidate_doi_url(rec: dict) -> str | None:
    doi = extract_clean_doi(rec.get("doi"))
    if doi and rec.get("source") != "official":
        return f"https://doi.org/{doi}"
    return None


def _derive_landing_from_url(url: str) -> list[str]:
    out = []
    if not url:
        return out
    u = url

    if "onlinelibrary.wiley.com/doi/pdfdirect/" in u:
        out.append(u.replace("/doi/pdfdirect/", "/doi/"))
    if "onlinelibrary.wiley.com/doi/pdf/" in u:
        out.append(u.replace("/doi/pdf/", "/doi/"))
    if "ahajournals.org/doi/pdf/" in u:
        out.append(u.replace("/doi/pdf/", "/doi/"))
    if "bmj.com/content/" in u and u.endswith(".full.pdf"):
        out.append(u[:-9])
    if "/article-pdf/" in u and u.lower().endswith(".pdf"):
        temp = u.replace("/article-pdf/", "/article/")
        parts = temp.split("/")
        if parts[-1].lower().endswith(".pdf") and len(parts) > 1:
            out.append("/".join(parts[:-1]))
    return out


def _save_snapshot_html(
    session: requests.Session,
    candidate_url: str,
    rec: dict,
    public_dir: Path,
    official_dir: Path,
    dedup: Deduplicator,
    logger,
) -> dict | None:
    if not candidate_url or not is_likely_relevant_url(candidate_url):
        return None
    if not _looks_html_candidate(candidate_url, rec.get("source")):
        return None

    try:
        logger.info("snapshot tentativa url=%s", candidate_url)
        r = session.get(candidate_url, timeout=25, allow_redirects=True)
        r.raise_for_status()
    except Exception as e:
        logger.info("snapshot falhou url=%s erro=%s", candidate_url, e)
        return None

    final_url = r.url
    ctype = (r.headers.get("Content-Type", "") or "").lower()
    content = r.content

    if "html" not in ctype and not _looks_like_html_bytes(content):
        return None
    if dedup.seen_content(content):
        return None

    root = official_dir if rec.get("source") == "official" else public_dir
    out = root / build_filename(
        rec.get("workstream", "na"),
        rec.get("source", "src"),
        rec.get("title", "doc"),
        final_url,
        "html",
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(content)

    logger.info("snapshot html salvo=%s", out)

    return {
        "url": rec.get("url", ""),
        "resolved_url": final_url,
        "path": str(out),
        "ext": "html",
        "source": rec.get("source", ""),
        "status": "ok_html_snapshot",
    }


def _try_snapshot_fallbacks(session, rec, raw_url, resolved_url, public_dir, official_dir, dedup, logger):
    candidates = []
    doi_url = _candidate_doi_url(rec)
    if doi_url:
        candidates.append(doi_url)
    candidates.extend(_derive_landing_from_url(resolved_url))
    candidates.extend(_derive_landing_from_url(raw_url))
    candidates.append(resolved_url)
    if raw_url != resolved_url:
        candidates.append(raw_url)

    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        snap = _save_snapshot_html(session, candidate, rec, public_dir, official_dir, dedup, logger)
        if snap:
            return snap
    return None


def download_records(records: list[dict], public_dir: Path, official_dir: Path, logger) -> tuple[list[dict], list[dict]]:
    dedup, man, failed = Deduplicator(), [], []
    s = requests.Session()
    s.headers.update(SESSION_HEADERS)

    for rec in records:
        raw_url = rec.get("url")
        if not isinstance(raw_url, str) or not raw_url:
            continue
        if dedup.seen_url(raw_url):
            continue

        resolved_url, resolved_kind = resolve_url(raw_url)
        st, ctype = _head(resolved_url)
        ext = infer_ext(resolved_url, ctype)

        if resolved_kind == "pdf" and ext == "bin":
            ext = "pdf"
        if resolved_kind == "html" and ext == "bin":
            ext = "html"

        if should_download(resolved_url, ext, rec.get("source")):
            root = official_dir if rec.get("source") == "official" else public_dir

            try:
                r = _request_with_retry(s, resolved_url, logger)
                final_url = r.url
                final_ctype = (r.headers.get("Content-Type", "") or "").lower()
                content = r.content

                final_ext = ext
                if final_ext == "pdf" and not _looks_like_pdf_bytes(content):
                    if "html" in final_ctype or _looks_like_html_bytes(content):
                        final_ext = "html"
                    else:
                        final_ext = "bin"

                if final_ext in {"html", "htm"} and not _looks_like_html_bytes(content) and "html" not in final_ctype:
                    snap = _try_snapshot_fallbacks(s, rec, raw_url, resolved_url, public_dir, official_dir, dedup, logger)
                    if snap:
                        man.append(snap)
                        continue

                if dedup.seen_content(content):
                    continue

                out = root / build_filename(
                    rec.get("workstream", "na"),
                    rec.get("source", "src"),
                    rec.get("title", "doc"),
                    final_url,
                    final_ext,
                )
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(content)

                logger.info("download ok path=%s", out)

                man.append(
                    {
                        "url": raw_url,
                        "resolved_url": final_url,
                        "path": str(out),
                        "ext": final_ext,
                        "source": rec.get("source", ""),
                        "status": "ok",
                    }
                )
                continue

            except Exception as e:
                logger.info("download falhou url=%s erro=%s", resolved_url, e)
                snap = _try_snapshot_fallbacks(s, rec, raw_url, resolved_url, public_dir, official_dir, dedup, logger)
                if snap:
                    man.append(snap)
                    continue

                failed.append(
                    {
                        "url": raw_url,
                        "resolved_url": resolved_url,
                        "status": "fail",
                        "reason": str(e),
                        "head_status": st,
                    }
                )
                continue

        logger.info("URLs filtradas: %s", resolved_url)
        snap = _try_snapshot_fallbacks(s, rec, raw_url, resolved_url, public_dir, official_dir, dedup, logger)
        if snap:
            man.append(snap)
            continue

        failed.append(
            {
                "url": raw_url,
                "resolved_url": resolved_url,
                "status": "filtered_no_snapshot",
                "reason": "filtered_and_no_html_snapshot",
                "head_status": st,
            }
        )

    return man, failed