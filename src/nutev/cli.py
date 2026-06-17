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

    serve = sub.add_parser("serve")
    serve.add_argument("--project-root", type=Path, required=True)
    serve.add_argument("--host", type=str, default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    platform_cmd = sub.add_parser("platform")
    platform_cmd.add_argument("--project-root", type=Path, required=True)
    platform_cmd.add_argument("--host", type=str, default="127.0.0.1")
    platform_cmd.add_argument("--port", type=int, default=8000)

    ask = sub.add_parser("ask", help="Ask questions over the article knowledge base")
    ask.add_argument("--project-root", type=Path, required=True)
    ask.add_argument("question", nargs="+", help="Your question about the corpus")
    ask.add_argument("--k", type=int, default=8, help="Number of articles to retrieve")
    ask.add_argument(
        "--backend",
        choices=["auto", "openai", "anthropic", "offline"],
        default="auto",
        help="LLM backend (default auto: OpenAI/Anthropic if a key is set, else offline)",
    )

    build_kb = sub.add_parser("build-kb", help="(Re)build the knowledge base from metadata_master.csv")
    build_kb.add_argument("--project-root", type=Path, required=True)

    tax = sub.add_parser("taxonomy", help="Manage the single-source-of-truth taxonomy (config/taxonomy.json)")
    tax.add_argument("action", choices=["validate", "build", "list"], help="validate, regenerate derived files, or list concepts")
    tax.add_argument("--config-root", type=Path, default=None, help="Config dir (default: bundled config/)")

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
            # Best-effort: pop the browser open once the server is up, so a local
            # user just runs `nutev serve` and the site appears. Skipped when
            # bound to all interfaces or when NUTEV_NO_BROWSER is set (Docker/CI).
            if args.host not in {"0.0.0.0"} and not os.environ.get("NUTEV_NO_BROWSER"):
                import threading
                import webbrowser

                def _open() -> None:
                    try:
                        webbrowser.open(landing)
                    except Exception:
                        pass

                threading.Timer(1.5, _open).start()
            uvicorn.run(app, host=args.host, port=args.port)
        except ModuleNotFoundError:
            print('FastAPI/uvicorn não estão instalados. Rode: pip install -e ".[platform]"')
        return

    if args.command == "taxonomy":
        from nutev.settings import default_config_root
        from nutev.taxonomy import build_all, concept_summary, load_taxonomy, validate_taxonomy

        config_root = args.config_root or default_config_root()
        if args.action == "validate":
            errors = validate_taxonomy(load_taxonomy(config_root))
            if errors:
                print("taxonomy.json is INVALID:")
                for err in errors:
                    print(f"  - {err}")
                raise SystemExit(1)
            print(f"taxonomy.json is valid ({config_root})")
        elif args.action == "build":
            written = build_all(config_root)
            print("Regenerated from taxonomy.json:")
            for name, path in written.items():
                print(f"  {name}: {path}")
        else:  # list
            for ctype, ids in concept_summary(load_taxonomy(config_root)).items():
                print(f"{ctype} ({len(ids)}): {', '.join(ids)}")
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
        from nutev.llm.chat_client import describe_backend, get_chat_client

        s = NutevSettings(project_root=args.project_root)
        if args.backend == "auto":
            client: object | str | None = "auto"
        elif args.backend == "offline":
            client = None
        else:
            client = get_chat_client(args.backend)
        result = answer(" ".join(args.question), s.output_dirs["11_knowledge_base"], k=args.k, client=client)
        label = result.get("backend") if args.backend == "auto" else describe_backend(args.backend)
        retrieval = result.get("retrieval")
        meta = f"[{result['mode']} | backend={label} | corpus={result['n_corpus']}"
        meta += f" | retrieval={retrieval}]" if retrieval else "]"
        print(meta + "\n")
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
