# NutEV Premium UI Guide

This guide describes the local visual layer for the NutEV Platform and Control Center.

## Landing page

Run:

```bash
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

The landing page links to the API docs, evidence matrix, claims, recommendations, human review queue, artifacts, and methods.

## Control Center

Run:

```bash
nutev dashboard --project-root ./project_output_demo --port 8501
```

The Control Center supports overview metrics, evidence inspection, audit claims, recommendation candidates, human review, provider status, export center, logs, and methods preview.

## Export Center

The Export Center surfaces key generated files, including metadata, evidence matrices, claims, recommendations, review queues, reports, and run logs.

## Provider Settings

Provider Settings is a visual status page for local providers and LLM-related configuration. Secrets should be provided through environment variables and must not be shown in full.

## Safety principles

- RecommendationCandidate is not a final recommendation.
- No final approval without human review.
- LLM output is assistive only.
- The platform is local-first.
- The UI does not approve protocol items automatically.
