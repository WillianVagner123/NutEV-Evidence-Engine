"""Optional semantic (embeddings) retrieval for the knowledge-base ask layer.

This module is a *fail-soft* enhancement layer over the deterministic TF-IDF
retrieval in :mod:`nutev.llm.ask`. It uses ``sentence-transformers`` to embed
documents and a ``faiss`` flat inner-product index for nearest-neighbour
search. Both dependencies are heavy and may not be installed (e.g. in the CI
virtualenv), and the first model load needs network access to download weights.

Every public entry point therefore degrades gracefully:

* :func:`is_available` returns ``False`` when network is disabled or when the
  optional dependencies are not importable.
* :func:`build_or_load_index` and :func:`semantic_retrieve` return ``None`` on
  *any* unavailability or failure, signalling the caller to fall back to the
  keyword retrieval.

All imports of the optional dependencies are performed lazily inside functions
so that importing this module is always cheap and safe offline.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "all-MiniLM-L6-v2"
TITLE_WEIGHT = 3
INDEX_FILENAME = "index.faiss"
META_FILENAME = "meta.json"


def _model_name() -> str:
    return os.environ.get("NUTEV_EMBED_MODEL") or DEFAULT_MODEL


def is_available() -> bool:
    """Report whether semantic retrieval can be attempted.

    Returns ``False`` when network access is disabled (the first model load may
    need to download weights) or when ``sentence-transformers`` / ``faiss`` are
    not importable. Imports are done lazily so this stays cheap offline.
    """

    if os.environ.get("NUTEV_DISABLE_NETWORK") == "1":
        return False
    try:
        import faiss  # noqa: F401
        import sentence_transformers  # noqa: F401
    except Exception:  # noqa: BLE001 - any import problem -> unavailable
        return False
    return True


@lru_cache(maxsize=1)
def _model():
    """Construct (and cache) the SentenceTransformer model.

    Imported lazily; callers must guard with :func:`is_available` first.
    """

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_model_name())


def _as_text(value: Any) -> str:
    """Flatten a possibly-missing string/list field into searchable text."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return " ".join(_as_text(item) for item in value)
    return str(value)


def _doc_text(record: dict) -> str:
    """Build the weighted searchable text for one document.

    The title is repeated ``TITLE_WEIGHT`` times to up-weight it, followed by
    abstract, journal and the categorical metadata fields.
    """

    title = _as_text(record.get("title")).strip()
    parts = [
        _as_text(record.get("abstract")),
        _as_text(record.get("journal")),
        _as_text(record.get("domains")),
        _as_text(record.get("outcomes")),
        _as_text(record.get("diet_patterns")),
        _as_text(record.get("clinical_conditions")),
    ]
    chunks = [title] * TITLE_WEIGHT if title else []
    chunks.extend(part for part in parts if part)
    return " ".join(chunks).strip()


def _content_hash(records: list[dict]) -> str:
    """Stable content hash over document_id + title + abstract of each record."""

    hasher = hashlib.sha256()
    for record in records:
        hasher.update(_as_text(record.get("document_id")).encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(_as_text(record.get("title")).encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(_as_text(record.get("abstract")).encode("utf-8"))
        hasher.update(b"\x01")
    return hasher.hexdigest()


def _doc_id(record: dict) -> str:
    return _as_text(record.get("document_id"))


def build_or_load_index(records: list[dict], kb_dir: str | Path):
    """Build or load a faiss index for ``records``, persisted under ``kb_dir``.

    Returns ``(faiss_index, id_order)`` where ``id_order`` is the list of
    ``document_id`` values in index order, or ``None`` on any failure or when
    semantic retrieval is unavailable. Fully fail-soft.

    A cached index is reused when ``<kb_dir>/embeddings/{index.faiss,meta.json}``
    exist and the meta's content hash and document count match ``records``.
    """

    if not records:
        return None

    embed_dir = Path(kb_dir) / "embeddings"
    index_path = embed_dir / INDEX_FILENAME
    meta_path = embed_dir / META_FILENAME

    content_hash = _content_hash(records)
    count = len(records)

    # Try to load a matching cached index first (cheap, no model needed).
    if index_path.is_file() and meta_path.is_file():
        try:
            import faiss

            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if (
                meta.get("hash") == content_hash
                and meta.get("count") == count
                and meta.get("model") == _model_name()
                and isinstance(meta.get("ids"), list)
                and len(meta["ids"]) == count
            ):
                index = faiss.read_index(str(index_path))
                return index, [str(i) for i in meta["ids"]]
        except Exception:  # noqa: BLE001 - corrupt/incompatible cache -> rebuild
            logger.debug("Failed to load cached embeddings index; rebuilding.")

    # Need to (re)build the index.
    if not is_available():
        return None

    try:
        import faiss
        import numpy as np

        ids = [_doc_id(rec) for rec in records]
        texts = [_doc_text(rec) for rec in records]
        model = _model()
        vectors = model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        vectors = np.asarray(vectors, dtype="float32")
        if vectors.ndim != 2 or vectors.shape[0] != count:
            return None

        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)

        # Persist index + metadata (best-effort; failure here is non-fatal).
        try:
            embed_dir.mkdir(parents=True, exist_ok=True)
            faiss.write_index(index, str(index_path))
            meta = {
                "hash": content_hash,
                "count": count,
                "model": _model_name(),
                "ids": ids,
            }
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:  # noqa: BLE001 - persistence is optional
            logger.debug("Failed to persist embeddings index; using in-memory.")

        return index, ids
    except Exception:  # noqa: BLE001 - any failure -> fall back to keyword
        logger.debug("Failed to build embeddings index.", exc_info=True)
        return None


def semantic_retrieve(
    records: list[dict],
    query: str,
    kb_dir: str | Path,
    k: int = 8,
) -> list[dict] | None:
    """Rank ``records`` against ``query`` using semantic similarity.

    Returns a list of shallow-copied records (top ``k``) each carrying a
    ``_retrieval_score`` cosine similarity, or ``None`` when semantic retrieval
    is unavailable or fails for any reason (caller should fall back to TF-IDF).
    """

    if not records:
        return None

    built = build_or_load_index(records, kb_dir)
    if built is None:
        return None
    index, id_order = built

    try:
        import numpy as np

        aligned = len(records) == len(id_order)
        by_id: dict[str, dict] = {}
        for rec in records:
            by_id.setdefault(_doc_id(rec), rec)

        model = _model()
        query_vec = model.encode(
            [query or ""],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        query_vec = np.asarray(query_vec, dtype="float32")
        if query_vec.ndim != 2:
            return None

        top_k = min(max(0, k), len(id_order))
        if top_k == 0:
            return []
        scores, indices = index.search(query_vec, top_k)

        results: list[dict] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(id_order):
                continue
            # Prefer positional mapping (handles duplicate/empty document ids);
            # fall back to id lookup only if the corpus order no longer aligns.
            if aligned and _doc_id(records[idx]) == id_order[idx]:
                record = records[idx]
            else:
                record = by_id.get(id_order[idx])
            if record is None:
                continue
            copy = dict(record)
            copy["_retrieval_score"] = float(score)
            results.append(copy)
        return results
    except Exception:  # noqa: BLE001 - any failure -> fall back to keyword
        logger.debug("Semantic retrieval failed.", exc_info=True)
        return None
