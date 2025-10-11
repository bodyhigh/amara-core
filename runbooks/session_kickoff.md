# Session Kickoff Runbook — Amara Core

This runbook defines the process for starting a new development session for the Amara Core project.

---

## 1. Load Context

- Paste the latest **Context Bundle (v1.1)** into the new chat.
- Ensure all sensitive values (tokens, secrets, credentials) are **redacted** before pasting.
- Verify that memory deltas, context_deltas, and developer logs are up to date.

---

## 2. Starting Prompt

Copy and paste this prompt into the first message of the new chat session:

```

You are resuming the Amara Core home chat.

1. Load the latest Context Bundle (v1.1).
2. Use the previous session’s closure summary as historical context.
3. Validate repository state, ensuring that:

   * All core services (litellm, qdrant, nginx, n8n) are healthy.
   * The docs/context and runbooks directories are synced with GitHub.
4. Announce readiness and propose the next 1–3 concrete tasks.

```

---

## 3. Pre-Flight Checks

- [ ] Verify `.env` is valid using `make env-check`.
- [ ] Ensure all containers are healthy via `docker compose ps`.
- [ ] Confirm that the `master` branch is clean (`git status` shows no pending changes).
- [ ] Run `make pre-commit` locally before new commits.
- [ ] If any issues appear, note them in the developer log before proceeding.

---

## 4. Kickoff Actions

1. Load `session_closure.md` from the previous session to carry over context.
2. Merge any open deltas from `tmp_delta.yaml` or staging branches.
3. Update `context_delta.log.yaml` if relevant.
4. Resume development at the first actionable next step.
5. Announce “Session Ready” in the chat.

---

## 5. References

- `runbooks/session_closure.md`
- `docs/context/context_delta.log.yaml`
- `docs/dev-logs/`
- `Makefile`
