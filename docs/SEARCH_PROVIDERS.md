# NutEV search providers

`src/nutev` is the canonical NutEV/NutMEV runtime. `src/local_deep_research` remains in the repository only as legacy/reference code.

## PubMed / NCBI

PubMed is executed through NCBI E-utilities with `esearch.fcgi` and `esummary.fcgi`. The canonical client uses `usehistory=y`, `WebEnv`, `query_key`, paginated `retstart`/`retmax` batches, retry/backoff for transient errors, and per-query checkpoints in `07_logs/checkpoints/pubmed/`.

Recommended variables:

- `NCBI_EMAIL`: recommended by NCBI. If absent, NutEV warns and uses conservative rate limiting.
- `ENTREZ_EMAIL`: fallback accepted by NutEV.
- `NCBI_API_KEY`: optional; increases allowed NCBI rate.
- `NCBI_TOOL`: defaults to `nutev_pipeline`.

Without an API key, NutEV sleeps about 0.40 seconds between NCBI requests. With an API key it sleeps about 0.13 seconds.

## Europe PMC, OpenAlex and Crossref

These scientific providers are independent of Google. Each provider has timeout/retry protection and failures are converted into provider failure events instead of crashing the pipeline. Use `OPENALEX_MAILTO` and `CROSSREF_MAILTO` where possible.

## Optional Google / gray literature

Google Programmable Search Engine, SerpAPI and Brave are optional gray-literature providers. They are skipped unless their API keys are configured. A Google quota/configuration failure does not invalidate the scientific search; PubMed, Europe PMC, OpenAlex, Crossref and official sources continue.

## Checkpoint / resume

Provider checkpoints are written under `07_logs/checkpoints/<provider>/`. PubMed checkpoints include the query hash, `WebEnv`, `query_key`, completed `retstart`, collected IDs, partial rows and status. Re-run with resume-enabled commands to continue from saved checkpoints without duplicating rows.

## Logs

Important provider observability files are in `07_logs`:

- `run_events.jsonl`: provider_started/provider_completed/provider_failed/provider_skipped/provider_partial events.
- `provider_failures.csv`: recoverable provider failures and skip reasons.
- `provider_performance.csv`: provider durations and returned rows.
- `run_summary.json`: high-level counts and partial/completed status.

## Optional provider implementations

The canonical runtime now includes optional clients for Google Programmable Search Engine (`google_pse`), SerpAPI (`serpapi`) and Brave Search (`brave`). They run only when their keys are present. Missing keys produce `status=skipped`, a `provider_skipped` event, and a recoverable row in `provider_failures.csv`; scientific providers continue normally.

Provider performance logs use these columns: `run_id`, `provider`, `workstream`, `query_hash`, `query`, `status`, `total_found`, `rows_returned`, `duration_seconds`, `resume_used`, and `checkpoint_path`. Failure logs include `stage`, `status`, `error_type`, `error_message`, `recoverable`, `fallback_used`, and `checkpoint_path`.

If `NUTEV_PUBMED_FETCH_ABSTRACTS=1`, PubMed additionally calls `efetch.fcgi` for XML abstracts. XML errors are logged as warnings and do not discard already collected `esummary` metadata.
