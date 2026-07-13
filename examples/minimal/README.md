# Minimal example — zero-key demo

The smallest way to see NutEV/NutMEV work, with **no API keys, no network, no real
data**.

```bash
python -m venv .venv
python -m pip install -e ".[dashboard]"
nutev demo-data --project-root ./project_output_demo
nutev dashboard --project-root ./project_output_demo
```

- `nutev demo-data` generates **synthetic** outputs (metadata, tables, logs, reports).
- `nutev dashboard` opens the Streamlit review UI at `http://localhost:8501`.

Outputs are a demonstration, **not** scientific evidence. See
[`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md) and
[`examples/article1_pilot/`](../article1_pilot/) for the Article 1 pilot.
