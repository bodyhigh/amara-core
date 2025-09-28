## Assessor Synthesis — Amara Core — Sprint N (v0.1.0 baseline)

### Convergent Findings

- (Single-source only for now; no cross-platform convergence yet.)
- Guardrails, proxy, and CI pipeline all validated as strong baselines.

### Divergent Findings

- None yet — waiting on additional platform assessments (e.g., Gemini, Claude, DeepSeek) to compare.

### Prioritization

- **Immediate Fix:**
  - Add smoke tests for `/api/llm/v1/chat/completions` and health endpoints.
  - Harden CORS to `amara.bodyhigh.com`.
- **Next Sprint:**
  - Add structured/rotated logs (`app_data/logs/*`).
  - Resolve n8n restart loop (stability).
- **Longer-term:**
  - Reintroduce Ollama for local fallback (reduce single-provider risk).
  - Extend unified error handling and input validation middleware.

### Guardrail Recommendations

- Strengthen **pre-commit suite**: add linter/formatter enforcement for JS/TS, not just headers.
- Introduce **CI smoke tests** hitting nginx-proxied LiteLLM endpoints.
- Extend `.env.example` with required dependency pins and clarifying notes.

### Strategic Roadmap

1. **Stabilize runtime** → Resolve n8n container loop, ensure Qdrant healthy, extend health checks.
2. **Close security gaps** → Lock down CORS, add structured logging, expand secret scanning.
3. **Improve test coverage** → Automate smoke tests, then expand into unit/e2e tests.
4. **Enable resiliency** → Reintroduce Ollama once GPU runtime is viable; configure model fallback in LiteLLM.
5. **Harden dev loop** → Document dependency pins, reduce Docker build friction, capture in onboarding docs.
