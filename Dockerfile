# syntax=docker/dockerfile:1
###############################################################################
# NutEV/NutMEV — lean image for the evidence pipeline CLI + local API.
#
# Replaces the former local_deep_research image (Flask + Node/Vite frontend +
# SQLCipher). nutev is a small Python CLI; this image installs the package and,
# by default, serves the local FastAPI app (`nutev serve`) on port 8000.
#
# Run the batch pipeline instead by overriding the command:
#   docker run --rm -v "$PWD/data:/data" nutev-nutmev \
#       --project-root /data --workstreams busca1
###############################################################################
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Extras baked into the image. Default ships the local API (`serve`/`platform`).
# Examples: "platform,dashboard" for the UI, or "all" for semantic+ocr+llm too.
ARG EXTRAS="platform"

# OCR (the `ocr` extra) additionally needs these system binaries. Uncomment when
# building with EXTRAS that include "ocr":
# RUN apt-get update && apt-get install -y --no-install-recommends \
#         tesseract-ocr poppler-utils \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# config/ (taxonomy + rules) is resolved relative to the source tree
# (settings.default_config_root -> <repo>/config), so we install the package
# editable and carry the repo into the image rather than building a wheel.
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY config/ ./config/

RUN pip install --upgrade pip \
    && if [ -n "$EXTRAS" ]; then pip install -e ".[$EXTRAS]"; else pip install -e .; fi

# Non-root runtime; own /app so best-effort caches (journal-quality metrics,
# predatory index) under config/ can be written, and /data for outputs.
RUN useradd --create-home --uid 10001 nutev \
    && mkdir -p /data \
    && chown -R nutev:nutev /app /data
USER nutev

# Project outputs (metadata, corpus, evidence tables, knowledge base) live here.
VOLUME /data
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/health').status==200 else 1)" || exit 1

ENTRYPOINT ["nutev"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000", "--project-root", "/data"]
