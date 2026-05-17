import csv


def _write_csv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    keys = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def export_watch_outputs(
    rows,
    new_rows,
    base_dir,
    run_dir,
    provider_perf=None,
    host_failures=None,
    capture_manifest=None,
):
    _write_csv(rows, base_dir / "global_watch_master.csv")
    _write_csv(new_rows, base_dir / "global_watch_new_items.csv")
    _write_csv(rows, run_dir / "global_watch_results.csv")
    _write_csv(new_rows, run_dir / "global_watch_new_items.csv")
    _write_csv(provider_perf or [], run_dir / "provider_performance.csv")
    _write_csv(host_failures or [], run_dir / "host_failures.csv")
    _write_csv(capture_manifest or [], run_dir / "capture_manifest.csv")
