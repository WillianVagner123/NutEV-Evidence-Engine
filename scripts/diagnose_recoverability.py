#!/usr/bin/env python3
"""P1 — CLI for the full-text recoverability diagnostic.

Measures the ceiling of recoverable full text BEFORE any fetcher runs.

Offline (default, no network):
    python scripts/diagnose_recoverability.py \
        --metadata project_output_final/02_metadata/article_data.csv \
        --outdir project_output_final/07_logs

Online (adds a live Unpaywall OA check per DOI; email is required by Unpaywall):
    UNPAYWALL_EMAIL=you@example.org python scripts/diagnose_recoverability.py \
        --metadata .../article_data.csv --outdir .../07_logs --online

Writes 07_logs/fulltext_recoverability.csv and fulltext_recoverability.json, and
prints the per-workstream open-access vs paywall ceiling.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Allow running from a checkout without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nutev.acquire.recoverability import (  # noqa: E402
    diagnose_recoverability,
    read_metadata_rows,
    recoverability_summary_block,
    write_recoverability_report,
    _write_json,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Full-text recoverability diagnostic (P1).")
    ap.add_argument("--metadata", required=True, help="Path to article_data.csv / metadata_master.csv")
    ap.add_argument("--outdir", default="07_logs", help="Directory for the report (default: 07_logs)")
    ap.add_argument("--online", action="store_true", help="Also query Unpaywall for OA (needs --email/UNPAYWALL_EMAIL)")
    ap.add_argument("--email", default=os.environ.get("UNPAYWALL_EMAIL"), help="Contact email for Unpaywall")
    ap.add_argument("--rate", type=float, default=0.1, help="Seconds between online requests (rate limit)")
    args = ap.parse_args()

    rows = read_metadata_rows(args.metadata)
    if not rows:
        print(f"Nenhuma linha em {args.metadata}", file=sys.stderr)
        return 1

    session = None
    if args.online:
        if not args.email:
            print("ERRO: --online exige --email ou a variável UNPAYWALL_EMAIL.", file=sys.stderr)
            return 2
        import requests  # local import so offline mode needs no network stack

        session = requests.Session()
        session.headers["User-Agent"] = "nutev-recoverability/1.0"
        _orig_get = session.get

        def _throttled_get(*a, **k):  # simple polite rate limit
            time.sleep(max(0.0, args.rate))
            return _orig_get(*a, **k)

        session.get = _throttled_get  # type: ignore[assignment]

    def _progress(done: int, total: int) -> None:
        if total and done % 25 == 0:
            print(f"  Unpaywall: {done}/{total}", file=sys.stderr)

    diagnosis = diagnose_recoverability(
        rows, online=args.online, email=args.email, session=session, progress=_progress
    )

    outdir = Path(args.outdir)
    csv_path = write_recoverability_report(diagnosis, outdir / "fulltext_recoverability.csv")
    json_path = _write_json(
        {**diagnosis, **recoverability_summary_block(diagnosis)},
        outdir / "fulltext_recoverability.json",
    )

    print(f"Registros: {diagnosis['total']}  |  modo: {'online' if args.online else 'offline'}")
    print(f"{'workstream':<14}{'total':>8}{'DOI%':>8}{'PMID%':>8}{'PMCID%':>8}{'OA%':>8}{'paywall%':>10}")
    for ws, s in diagnosis["per_workstream"].items():
        print(f"{ws:<14}{s['total']:>8}{s['pct_doi']:>8}{s['pct_pmid']:>8}{s['pct_pmcid']:>8}{s['pct_open_access']:>8}{s['pct_likely_paywall']:>10}")
    ov = diagnosis["overall"]
    print(f"{'TOTAL':<14}{diagnosis['total']:>8}{'':>8}{'':>8}{'':>8}{ov['pct_open_access']:>8}{ov['pct_likely_paywall']:>10}")
    print(f"\nRelatórios: {csv_path}  |  {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
