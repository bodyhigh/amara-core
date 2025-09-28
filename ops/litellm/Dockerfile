# ops/litellm/Dockerfile
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build toolchain + curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make \
    libffi-dev libssl-dev python3-dev pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir "litellm[proxy]==1.44.2"

RUN useradd -ms /bin/bash appuser
USER appuser

EXPOSE 4000
CMD ["litellm", "--port", "4000", "--host", "0.0.0.0"]
