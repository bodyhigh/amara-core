## Assessment Report — Amara Core — Sprint N (v0.1.0)

### Strengths

- ✅ **Infra hardening achieved**: LiteLLM proxy stable with OpenAI-only config; NGINX reverse proxy configured SSE-safe (no buffering/gzip).
- ✅ **Guardrails working**: pre-commit hooks enforce Amara script headers, block legacy `docker[dash]compose`, and catch secret patterns.
- ✅ **Green CI pipeline**: all checks pass on `master`; reproducible onboarding validated.
- ✅ **Onboarding improved**: `.env.example` updated, README includes Environment Setup.
- ✅ **Docs & logs aligned**: context_delta and devlog entries updated; tagged baseline (`v0.1.0`) captured.

### Weaknesses

- ⚠️ **Limited test coverage**: no automated smoke tests yet for `/api/llm/v1/chat/completions` or other runtime endpoints.
- ⚠️ **n8n container restart loop**: unresolved runtime issue in stack.
- ⚠️ **CORS defaults open**: not yet restricted to `amara.bodyhigh.com`.
- ⚠️ **Logging gap**: no structured/rotated access logs in place.

### Risks

- ❌ **Single-provider fragility**: stack depends solely on OpenAI; no local fallback (Ollama disabled).
- ⚠️ **Security exposure**: until CORS is locked down and secrets handling extended, proxy may be overly permissive.
- ⚠️ **Observability blind spot**: without structured logs/metrics, diagnosing issues at runtime will be hard.

### Surprises

- 🎉 Pre-commit header validator already caught missing metadata in JS files — saved drift before merge.
- 🚨 Dependency conflicts (litellm/uvicorn) required pinning; not yet documented in README/requirements.

### Quality Gate Review

| Gate              | Status | Notes                                                        |
| ----------------- | ------ | ------------------------------------------------------------ |
| Security          | ⚠️     | Proxy auth works, but CORS + key mgmt need tightening.       |
| API Contracts     | ⚠️     | LiteLLM health OK, but no formal API schema/tests yet.       |
| Input Validation  | ❌     | None implemented for inbound routes.                         |
| Logging           | ⚠️     | NGINX basics only; no structured/rotated logs.               |
| Errors            | ⚠️     | Basic HTTP errors handled; no unified error middleware.      |
| Tests             | ❌     | Only manual curl checks; no automated test suite.            |
| Style/Conventions | ✅     | Pre-commit enforcing headers, style, and forbidden patterns. |

### Recommendations

- **Add smoke test suite**: target `/api/llm/health` and `/api/llm/v1/chat/completions` (streaming).
- **Harden CORS**: restrict to `amara.bodyhigh.com` in nginx.conf.
- **Add structured logging**: configure JSON logs + rotation under `app_data/logs/`.
- **Track n8n restart issue**: inspect logs, add minimal health check, consider moving out-of-band if unstable.
- **Document dependency pins**: record `litellm==1.44.2` / `uvicorn<0.23` workaround in requirements/README.

### Process Friction

- Docker build loops due to native deps (madoka/gcc/uvicorn conflict) slowed iteration.
- Pre-commit header enforcement initially failed due to mismatched schema (JS vs Python header style).
- Context_delta schema errors highlighted YAML formatting drift — needed fixes before commit.
