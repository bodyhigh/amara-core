# LiteLLM Proxy — Amara Core

LiteLLM runs as an **OpenAI-compatible API proxy** so Amara agents can call multiple backends
(OpenAI, Ollama, local) through a single `/api/llm/*` endpoint via NGINX.

---

## Service Overview

- **Port:** `4000` (proxied as `/api/llm/` by NGINX)
- **Auth:** Requires `Authorization: Bearer $LITELLM_PROXY_KEY` for all requests when a
  `LITELLM_MASTER_KEY` is set (we set this from `.env`).
- **Config:** Mounted at `/etc/litellm/config.yaml` from `ops/litellm/config.yaml`
- **Health:** `/health` endpoint checks model backends are reachable.

---

## Configuration

### `.env`

```ini
# LiteLLM service
LITELLM_PORT=4000
# Generate a strong admin key:
#   echo "LITELLM_PROXY_KEY=$(openssl rand -hex 24)" >> .env
LITELLM_PROXY_KEY=...
OPENAI_API_KEY=sk-...
```

### `ops/litellm/config.yaml`

Current repo ships with a minimal OpenAI-only config:

```yaml
model_list:
  - model_name: openai/main
    litellm_params:
      model: openai/gpt-4o
      # api_key comes from env OPENAI_API_KEY

model_groups:
  - name: chat-default
    models: [openai/main]
    fallback: true
```

To add Ollama backends later, re-enable the `ollama` service in `compose.yml` and
add entries like:

```yaml
- model_name: local/llama3.1-8b
  litellm_params:
    model: ollama/llama3.1:8b
    api_base: http://ollama:11434
    api_key: ollama
```

---

## Usage

### Health check

```bash
# Upstream
curl -H "Authorization: Bearer $LITELLM_PROXY_KEY" http://127.0.0.1:4000/health

# Through NGINX
curl -H "Authorization: Bearer $LITELLM_PROXY_KEY" http://127.0.0.1:${NGINX_HTTP_PORT:-8080}/api/llm/health
```

### Chat completion

```bash
curl -s http://127.0.0.1:${NGINX_HTTP_PORT:-8080}/api/llm/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "model": "openai/main",
        "messages": [{"role": "user", "content": "Hello from Amara Core!"}]
      }'
```

---

## Notes

- NGINX forwards `Authorization` → LiteLLM, so the master key is required even via `/api/llm/`.
- For development you can comment out `LITELLM_MASTER_KEY` in `compose.yml` to disable auth
  (do **not** do this in a public deployment).
- Healthcheck inside Compose now uses the Bearer token, so containers report healthy.
