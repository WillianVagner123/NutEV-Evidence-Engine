from __future__ import annotations
from pathlib import Path
import time
import requests

from nutev.download.dedup import Deduplicator
from nutev.download.filters import should_download
from nutev.download.naming import build_filename, infer_ext
from nutev.download.resolver import resolve_url


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
            r = session.get(url, timeout=20, allow_redirects=True)
            r.raise_for_status()
            return r.content
        except Exception as e:
            last = e
            time.sleep(0.5 * attempt)
    raise RuntimeError(f"download failed after retries: {last}")


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

        if not should_download(resolved_url, ext, rec.get("source")):
            logger.info("URLs filtradas: %s", resolved_url)
            continue

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
        except Exception as e:
            failed.append(
                {
                    "url": raw_url,
                    "resolved_url": resolved_url,
                    "status": "fail",
                    "reason": str(e),
                    "head_status": st,
                }
            )

    return man, failed