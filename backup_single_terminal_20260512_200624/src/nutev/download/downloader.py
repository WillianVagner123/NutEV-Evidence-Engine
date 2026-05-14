from __future__ import annotations
from pathlib import Path
from urllib.parse import urlparse
import time
import requests

from nutev.download.dedup import Deduplicator
from nutev.download.filters import should_download
from nutev.download.naming import build_filename, infer_ext
from nutev.download.resolver import resolve_url


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
}


def _head(url: str, timeout: int = 10) -> tuple[int, str]:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code, r.headers.get("Content-Type", "")
    except Exception:
        return 0, ""


def _get_with_retry(session: requests.Session, url: str, logger, retries: int = 3) -> bytes:
    last = None
    for attempt in range(1, retries + 1):
        try:
            logger.info("download tentativa=%d url=%s", attempt, url)
            r = session.get(url, timeout=25, allow_redirects=True)
            r.raise_for_status()
            return r.content
        except Exception as e:
            last = e
            time.sleep(0.75 * attempt)
    raise RuntimeError(f"download failed after retries: {last}")


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
    htmlish = [
        "/article",
        "/articles",
        "/doi/",
        "/content/",
        "/journal/",
        "/journals/",
        "guideline",
        "statement",
        "consensus",
        "framework",
        "questionnaire",
        "recommendation",
    ]
    return any(tok in u for tok in htmlish)


def _save_snapshot_html(
    session: requests.Session,
    candidate_url: str,
    rec: dict,
    public_dir: Path,
    official_dir: Path,
    dedup: Deduplicator,
    logger,
) -> dict | None:
    if not _looks_html_candidate(candidate_url, rec.get("source")):
        return None

    try:
        logger.info("snapshot tentativa url=%s", candidate_url)
        r = session.get(candidate_url, timeout=25, allow_redirects=True)
        r.raise_for_status()
    except Exception as e:
        logger.info("snapshot falhou url=%s erro=%s", candidate_url, e)
        return None

    ctype = (r.headers.get("Content-Type", "") or "").lower()
    final_url = r.url

    if "html" not in ctype and "<html" not in r.text.lower():
        return None

    content = r.content
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


def download_records(records: list[dict], public_dir: Path, official_dir: Path, logger) -> tuple[list[dict], list[dict]]:
    dedup, man, failed = Deduplicator(), [], []
    s = requests.Session()

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

        # caminho normal
        if should_download(resolved_url, ext, rec.get("source")):
            root = official_dir if rec.get("source") == "official" else public_dir
            out = root / build_filename(
                rec.get("workstream", "na"),
                rec.get("source", "src"),
                rec.get("title", "doc"),
                resolved_url,
                ext,
            )

            try:
                content = _get_with_retry(s, resolved_url, logger)
                if dedup.seen_content(content):
                    continue

                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(content)

                logger.info("download ok path=%s", out)

                man.append(
                    {
                        "url": raw_url,
                        "resolved_url": resolved_url,
                        "path": str(out),
                        "ext": ext,
                        "source": rec.get("source", ""),
                        "status": "ok",
                    }
                )
                continue
            except Exception as e:
                logger.info("download falhou url=%s erro=%s", resolved_url, e)

                # fallback: tenta salvar a página html do resolved_url
                snap = _save_snapshot_html(
                    s,
                    resolved_url,
                    rec,
                    public_dir,
                    official_dir,
                    dedup,
                    logger,
                )
                if snap:
                    man.append(snap)
                    continue

                # fallback extra: tenta a url bruta original
                if raw_url != resolved_url:
                    snap = _save_snapshot_html(
                        s,
                        raw_url,
                        rec,
                        public_dir,
                        official_dir,
                        dedup,
                        logger,
                    )
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

        # se foi filtrado para binário/pdf, ainda tenta snapshot html quando parecer artigo importante
        logger.info("URLs filtradas: %s", resolved_url)

        snap = _save_snapshot_html(
            s,
            resolved_url,
            rec,
            public_dir,
            official_dir,
            dedup,
            logger,
        )
        if snap:
            man.append(snap)
            continue

        if raw_url != resolved_url:
            snap = _save_snapshot_html(
                s,
                raw_url,
                rec,
                public_dir,
                official_dir,
                dedup,
                logger,
            )
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