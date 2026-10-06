# ---------------------------------------------------------------------------
# rent-map-live — Docker image for Coolify deployment.
# This file is ADDITIVE: the existing Vercel deployment does not use it.
#
# Runtime flow (mirrors current Vercel behavior):
#   1. python build.py     -> generates dist/ (index.html, app.js, style.css)
#                             by injecting env vars into the placeholders.
#                             Runs at container START so no secrets are ever
#                             baked into the image.
#   2. uvicorn index:app   -> serves API routes + the generated dist/ files.
# ---------------------------------------------------------------------------

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Python dependencies — same requirements.txt used by Vercel.
COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# Application code + frontend source files ONLY.
# Secrets are intentionally NOT copied into the image; they are supplied at
# runtime via Coolify environment variables.
# (.dockerignore excludes .git, dist/, .env*, etc. from the build context.)
COPY index.py build.py app.js index.html style.css ./

EXPOSE 8000

# Fails fast with a clear message if a required env var is missing:
#   - build.py raises RuntimeError("Missing GOOGLE_MAPS_API_KEY / SUPABASE_URL /
#     SUPABASE_ANON_KEY") before uvicorn starts if build vars are absent.
#   - index.py raises KeyError at import if GROQ_API_KEY or SUPABASE_DB_URL
#     are absent.
# Existing health endpoint: GET / serves dist/index.html (no app code changes).
CMD ["sh", "-c", "python build.py && exec uvicorn index:app --host 0.0.0.0 --port 8000"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=5)"