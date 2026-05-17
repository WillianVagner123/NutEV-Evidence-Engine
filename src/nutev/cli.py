from __future__ import annotations

import argparse
import os
from pathlib import Path

from nutev.logs import setup_logger
from nutev.settings import NutevSettings


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    gw = sub.add_parser("global-watch")
    gw.add_argument("--project-root", type=Path, required=True)
    gw.add_argument("--since-days", type=int, default=7)
    gw.add_argument("--mode", choices=["quick", "thesis", "exhaustive"], default="quick")
    gw.add_argument("--web-enabled", action="store_true")
    gw.add_argument("--official-crawl", action="store_true")
    gw.add_argument("--country-discovery", action="store_true")
    gw.add_argument("--llm-enabled", action="store_true")
    gw.add_argument("--resume", action="store_true")
    gw.add_argument("--notify-webhook", action="store_true")
    gw.add_argument("--webhook-url", type=str, default=None)
    gw.add_argument("--capture-enabled", action="store_true")
    gw.add_argument("--capture-limit", type=int, default=None)

    p.add_argument("--project-root", type=Path)
    p.add_argument("--workstreams", nargs="+", default=["busca1", "busca2a", "busca2b", "a3"])
    p.add_argument("--web-enabled", action="store_true")
    args = p.parse_args()

    if args.command == "global-watch":
        from nutev.global_watch.watch_pipeline import run_global_watch

        if not getattr(args, "web_enabled", False):
            os.environ["NUTEV_DISABLE_NETWORK"] = "1"
        s = NutevSettings(
            project_root=args.project_root,
            web_enabled=args.web_enabled,
            mode=args.mode,
            since_days=args.since_days,
            llm_enabled=args.llm_enabled,
        )
        for d in s.output_dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        logger = setup_logger(s.output_dirs["07_logs"])
        result = run_global_watch(
            s,
            logger,
            args.since_days,
            args.mode,
            args.resume,
            args.official_crawl,
            args.country_discovery,
            args.llm_enabled,
            capture_enabled=args.capture_enabled,
            capture_limit=args.capture_limit,
            notify_webhook=args.notify_webhook,
            webhook_url=args.webhook_url,
        )
        logger.info("Global watch: %s", result)
        return

    if not args.project_root:
        p.error("--project-root is required for default pipeline mode")

    from nutev.pipelines.master_pipeline import run_pipeline

    s = NutevSettings(project_root=args.project_root, web_enabled=args.web_enabled)
    for d in s.output_dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(s.output_dirs["07_logs"])
    result = run_pipeline(s, args.workstreams, logger)
    logger.info("Resumo: %s", result)


if __name__ == "__main__":
    main()
