from __future__ import annotations
import argparse
from pathlib import Path
from nutev.settings import NutevSettings
from nutev.logs import setup_logger
from nutev.pipelines.master_pipeline import run_pipeline


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--workstreams", nargs="+", default=["busca1", "busca2a", "busca2b", "a3"])
    p.add_argument("--web-enabled", action="store_true")
    args = p.parse_args()

    s = NutevSettings(project_root=args.project_root, web_enabled=args.web_enabled)
    for d in s.output_dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    logger = setup_logger(s.output_dirs["07_logs"])
    result = run_pipeline(s, args.workstreams, logger)
    logger.info("Resumo: %s", result)


if __name__ == "__main__":
    main()
