# PubMed troubleshooting

## PubMed E-utilities request failed

Try the following:

1. Set `NCBI_EMAIL` in `.env` or in your shell.
2. Optionally set `NCBI_API_KEY` for higher rate limits.
3. Keep `NCBI_TOOL=nutev_pipeline` or set your own tool name.
4. Reduce `NUTEV_PUBMED_BATCH_SIZE` if the network is unstable.
5. Re-run with resume so NutEV can continue from `07_logs/checkpoints/pubmed/`.
6. Inspect `07_logs/provider_failures.csv` and `07_logs/run_events.jsonl`.

## Missing NCBI_EMAIL

NutEV does not crash. It logs a warning and uses conservative PubMed rate limiting.

## Google stopped / quota / missing API key

Google is optional. Configure `GOOGLE_API_KEY` and `GOOGLE_CSE_ID`, configure `SERPAPI_API_KEY`, or ignore Google for the scientific search. Missing or failing Google providers are logged as skipped/failed and the pipeline continues.
