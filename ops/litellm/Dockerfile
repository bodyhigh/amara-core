# ops/litellm/Dockerfile
FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# curl for healthcheck; clean afterward
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# litellm proxy + uvicorn server
RUN pip install --no-cache-dir "litellm[proxy]>=1.44.0" "uvicorn[standard]"

WORKDIR /app
EXPOSE 4000

# actual startup command is set in compose to allow ${LITELLM_PORT}
