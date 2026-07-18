"""Corpus-level report: fuzzy (content) dedup, thematic clustering, heatmap.

The pipeline already deduplicates by identifier (DOI/PMID/title) and codes A/B/C/D
per document. This adds the *corpus* view your scoping script produced:

- **Fuzzy dedup** — TF-IDF + cosine over each document's text signature, grouping
  near-duplicates that identifier-dedup misses (translations, re-issues, the same
  guide mirrored on several sites), via union-find.
- **Thematic clustering** — KMeans over the same vectors, so the corpus is grouped
  by content, not just by country.
- **Theme heatmap** — A/B/C/D presence per cluster, saved as a PNG, plus a
  multi-sheet Excel (documents, dup pairs, per-cluster theme means, summary).

scikit-learn and matplotlib are optional (`pip install -e ".[report]"`). When
absent, :func:`write_corpus_report` returns a clear "skipped" result with an
install hint instead of failing — nothing else in the pipeline depends on it.
Every output is assistive and enters human review.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

_THEME_COLS = ("domain_A", "domain_B", "domain_C", "domain_D")


def report_dependencies_available() -> bool:
    """Whether scikit-learn + matplotlib are importable."""
    try:
        import matplotlib  # noqa: F401
        import sklearn  # noqa: F401

        return True
    except Exception:
        return False


def _doc_signature(row: dict) -> str:
    """Text signature for a document: full text when available, else the coded
    key phrases + top terms + title (always present, even from the checkpoint)."""
    text = str(row.get("extracted_text") or "").strip()
    if text:
        return text
    parts = [
        str(row.get("name") or row.get("title") or ""),
        str(row.get("key_phrases_text") or ""),
        str(row.get("top_terms") or "").replace("|", " "),
    ]
    return " ".join(p for p in parts if p).strip()


def _tfidf(signatures: list[str]):
    from sklearn.feature_extraction.text import TfidfVectorizer

    # min_df=1: corpora here are small; multi-language so no stop words.
    vectorizer = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), min_df=1)
    return vectorizer.fit_transform(signatures)


def fuzzy_dedup(rows: list[dict], *, threshold: float = 0.9, min_chars: int = 200) -> tuple[list[dict], list[dict]]:
    """Group near-duplicate documents by TF-IDF cosine similarity.

    Adds ``dedup_group`` and ``dedup_is_duplicate_of`` to each eligible row (the
    representative of a group is the longest document). Returns
    ``(rows, duplicate_pairs)``; a pair is ``{i,j,similarity}``. Rows too short to
    compare are left ungrouped. Requires scikit-learn.
    """
    from sklearn.metrics.pairwise import cosine_similarity

    idx = [i for i, r in enumerate(rows) if len(_doc_signature(r)) >= min_chars]
    if len(idx) < 2:
        return rows, []

    sims = cosine_similarity(_tfidf([_doc_signature(rows[i]) for i in idx]))

    parent = list(range(len(idx)))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    pairs: list[dict] = []
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            if sims[a, b] >= threshold:
                parent[find(a)] = find(b)
                pairs.append({
                    "i": rows[idx[a]].get("name", idx[a]),
                    "j": rows[idx[b]].get("name", idx[b]),
                    "similarity": round(float(sims[a, b]), 4),
                })

    groups: dict[int, list[int]] = {}
    for pos, original in enumerate(idx):
        groups.setdefault(find(pos), []).append(original)

    gid = 0
    for members in groups.values():
        gid += 1
        label = f"G{gid:04d}"
        rep = max(members, key=lambda i: len(_doc_signature(rows[i])))
        for i in members:
            rows[i]["dedup_group"] = label
            rows[i]["dedup_is_duplicate_of"] = "" if i == rep else str(rows[rep].get("name", rep))
    return rows, pairs


def cluster_corpus(rows: list[dict], *, n_clusters: int = 10, min_chars: int = 200) -> list[dict]:
    """Assign a ``cluster_id`` to each document via KMeans over TF-IDF. Uses only
    non-duplicate representatives; k adapts to corpus size. Requires scikit-learn."""
    import math

    from sklearn.cluster import KMeans

    base = [
        i for i, r in enumerate(rows)
        if len(_doc_signature(r)) >= min_chars and not r.get("dedup_is_duplicate_of")
    ]
    if len(base) < 5:
        return rows

    k = min(n_clusters, max(2, int(math.sqrt(len(base)))))
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(
        _tfidf([_doc_signature(rows[i]) for i in base])
    )
    for pos, original in enumerate(base):
        rows[original]["cluster_id"] = int(labels[pos])
    return rows


def _theme_pivot(rows: list[dict]):
    """Per-cluster mean presence of each A/B/C/D domain (representatives only)."""
    import pandas as pd

    reps = [r for r in rows if not r.get("dedup_is_duplicate_of")]
    if not reps:
        return pd.DataFrame(columns=list(_THEME_COLS))
    frame = pd.DataFrame([
        {
            "cluster_id": r.get("cluster_id", "NA"),
            **{c: 1 if bool(r.get(c)) else 0 for c in _THEME_COLS},
        }
        for r in reps
    ])
    if frame["cluster_id"].nunique() > 1 or frame["cluster_id"].iloc[0] != "NA":
        return frame.groupby("cluster_id")[list(_THEME_COLS)].mean().sort_index()
    pivot = frame[list(_THEME_COLS)].mean().to_frame().T
    pivot.index = ["ALL"]
    return pivot


def _save_heatmap(pivot, out_png: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")  # headless
    import matplotlib.pyplot as plt

    plt.figure(figsize=(8, max(3, 0.6 * len(pivot.index))))
    plt.imshow(pivot.values, aspect="auto", vmin=0, vmax=1)
    plt.yticks(range(len(pivot.index)), [str(i) for i in pivot.index])
    plt.xticks(range(len(pivot.columns)), list(pivot.columns), rotation=45, ha="right")
    plt.colorbar(label="Proporção de documentos com o domínio (0–1)")
    plt.title("Domínios A/B/C/D por cluster")
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def write_corpus_report(
    rows: list[dict],
    out_dir: str | Path,
    *,
    threshold: float = 0.9,
    n_clusters: int = 10,
    logger: Any | None = None,
) -> dict:
    """Run fuzzy dedup + clustering, then write the Excel report and heatmap.

    Degrades gracefully: if scikit-learn/matplotlib are missing, returns
    ``{"status": "skipped", "reason": ...}`` with an install hint and writes
    nothing. Otherwise returns counts and the output paths.
    """
    if not report_dependencies_available():
        hint = 'pip install -e ".[report]"  (scikit-learn + matplotlib)'
        if logger:
            logger.info("relatório de corpus pulado — dependências ausentes: %s", hint)
        return {"status": "skipped", "reason": "missing scikit-learn/matplotlib", "install": hint}

    import pandas as pd

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, pairs = fuzzy_dedup(rows, threshold=threshold)
    rows = cluster_corpus(rows, n_clusters=n_clusters)
    pivot = _theme_pivot(rows)

    png_path = out_dir / "NUTEV_GUIDES_THEME_HEATMAP.png"
    try:
        if not pivot.empty:
            _save_heatmap(pivot, png_path)
    except Exception as exc:  # pragma: no cover - plotting is best-effort
        if logger:
            logger.warning("não consegui salvar heatmap: %s", exc)

    doc_cols = [
        "name", "country", "reference", "profile", "n_domains",
        *(_THEME_COLS), "cluster_id", "dedup_group", "dedup_is_duplicate_of",
        "n_key_phrases", "top_terms",
    ]
    docs_df = pd.DataFrame([{c: r.get(c, "") for c in doc_cols} for r in rows])

    n_groups = len({r.get("dedup_group") for r in rows if r.get("dedup_group")})
    n_dups = sum(1 for r in rows if r.get("dedup_is_duplicate_of"))
    xlsx_path = out_dir / "NUTEV_GUIDES_REPORT.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        docs_df.to_excel(writer, sheet_name="DOCUMENTS", index=False)
        if pairs:
            pd.DataFrame(pairs).sort_values("similarity", ascending=False).to_excel(
                writer, sheet_name="DUPLICATES", index=False
            )
        if not pivot.empty:
            pivot.to_excel(writer, sheet_name="THEME_BY_CLUSTER")

    result = {
        "status": "ok",
        "documents": len(rows),
        "dedup_groups": n_groups,
        "duplicates_marked": n_dups,
        "duplicate_pairs": len(pairs),
        "clusters": len({r.get("cluster_id") for r in rows if r.get("cluster_id") is not None}),
        "report_xlsx": str(xlsx_path),
        "heatmap_png": str(png_path) if png_path.exists() else "",
    }
    if logger:
        logger.info("relatório de corpus: %s", result)
    return result
