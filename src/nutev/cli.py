from __future__ import annotations

import argparse
import os
import subprocess
import sys
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

    dash = sub.add_parser("dashboard")
    dash.add_argument("--project-root", type=Path, required=True)
    dash.add_argument("--port", type=int, default=8501)

    demo = sub.add_parser("demo-data")
    demo.add_argument("--project-root", type=Path, required=True)

    serve = sub.add_parser("serve")
    serve.add_argument("--project-root", type=Path, required=True)
    serve.add_argument("--host", type=str, default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    platform_cmd = sub.add_parser("platform")
    platform_cmd.add_argument("--project-root", type=Path, required=True)
    platform_cmd.add_argument("--host", type=str, default="127.0.0.1")
    platform_cmd.add_argument("--port", type=int, default=8000)

    pilot = sub.add_parser("pilot-report")
    pilot.add_argument("--project-root", type=Path, required=True)

    prize = sub.add_parser("prize-metrics")
    prize.add_argument("--project-root", type=Path, required=True)

    ask = sub.add_parser("ask", help="Ask questions over the article knowledge base")
    ask.add_argument("--project-root", type=Path, required=True)
    ask.add_argument("question", nargs="+", help="Your question about the corpus")
    ask.add_argument("--k", type=int, default=8, help="Number of articles to retrieve")

    build_kb = sub.add_parser("build-kb", help="(Re)build the knowledge base from metadata_master.csv")
    build_kb.add_argument("--project-root", type=Path, required=True)

    p.add_argument("--project-root", type=Path)
    p.add_argument("--workstreams", nargs="+", default=["busca1", "busca2a", "busca2b", "a3"])
    p.add_argument("--web-enabled", action="store_true")
    p.add_argument("--llm-enabled", action="store_true")
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

    if args.command == "dashboard":
        dashboard_path = Path(__file__).parent / "ui" / "dashboard.py"
        url = f"http://localhost:{args.port}"
        print(url)
        try:
            __import__("streamlit")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(dashboard_path),
                    "--server.port",
                    str(args.port),
                    "--",
                ],
                check=True,
                env={**os.environ, "NUTEV_DASHBOARD_PROJECT_ROOT": str(args.project_root)},
            )
        except ModuleNotFoundError:
            print('Streamlit não está instalado. Rode: pip install -e ".[dashboard]"')
        except Exception:
            print(url)
        return

    if args.command == "demo-data":
        from nutev.demo.demo_data import generate_demo_data

        generate_demo_data(args.project_root)
        print(f"Demo data generated at: {args.project_root}")
        return

    if args.command in {"serve", "platform"}:
        landing = f"http://{args.host}:{args.port}"
        if args.host == "0.0.0.0":
            print("Atenção: você está expondo a API na rede. Use apenas em ambiente controlado.")
        print(f"Landing page: {landing}")
        print(f"API docs: {landing}/docs")
        print(f"Redoc: {landing}/redoc")
        try:
            __import__("fastapi")
            __import__("uvicorn")
            from nutev.api.server import create_app
            import uvicorn

            app = create_app(args.project_root)
            uvicorn.run(app, host=args.host, port=args.port)
        except ModuleNotFoundError:
            print('FastAPI/uvicorn não estão instalados. Rode: pip install -e ".[platform]"')
        return

    if args.command == "pilot-report":
        from nutev.export.pilot_report import generate_pilot_report

        path = generate_pilot_report(args.project_root)
        print(f"Pilot report generated: {path}")
        return

    if args.command == "prize-metrics":
        from nutev.export.prize_metrics import write_prize_metrics_summary

        path = write_prize_metrics_summary(args.project_root)
        print(f"Prize metrics generated: {path}")
        print(f"Prize metrics text: {path.with_suffix('.txt')}")
        return

    if args.command == "build-kb":
        from nutev.export.kb_aggregations import write_aggregations
        from nutev.export.knowledge_base import load_kb_records_from_metadata_csv, write_knowledge_base

        s = NutevSettings(project_root=args.project_root)
        kb_dir = s.output_dirs["11_knowledge_base"]
        records = load_kb_records_from_metadata_csv(s.output_dirs["02_metadata"] / "metadata_master.csv")
        write_knowledge_base(records, kb_dir)
        write_aggregations(records, kb_dir / "summary")
        print(f"Knowledge base rebuilt: {len(records)} records -> {kb_dir}")
        return

    if args.command == "ask":
        from nutev.llm.ask import answer

        s = NutevSettings(project_root=args.project_root)
        result = answer(" ".join(args.question), s.output_dirs["11_knowledge_base"], k=args.k)
        print(f"[{result['mode']} | backend={result['backend']} | corpus={result['n_corpus']}]\n")
        print(result["answer"])
        if result["citations"]:
            print("\nSources:")
            for c in result["citations"]:
                where = ", ".join(c.get("countries") or []) or "—"
                print(f"  [{c['index']}] {c['title']} ({c.get('year') or 'n/a'}; {where}; {c.get('journal') or '—'}) {c.get('url') or c.get('doi') or ''}")
        return

    if not args.project_root:
        p.error("--project-root is required for default pipeline mode")

    from nutev.pipelines.master_pipeline import run_pipeline

    s = NutevSettings(
        project_root=args.project_root,
        web_enabled=args.web_enabled,
        llm_enabled=args.llm_enabled,
    )
    for d in s.output_dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(s.output_dirs["07_logs"])
    result = run_pipeline(s, args.workstreams, logger)
    logger.info("Resumo: %s", result)


if __name__ == "__main__":
    main()
