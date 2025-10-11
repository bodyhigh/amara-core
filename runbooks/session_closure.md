# Session Closure Runbook — Amara Core

This runbook defines the process for cleanly closing out a development session for the Amara Core project.

---

## 1. Update Logs

- Use `make context-delta` to append a structured YAML snippet to
  `docs/context/context_delta.log.yaml`.
- Append or merge any changes into the appropriate developer log file under
  `docs/dev-logs/` (e.g., `devlog_2025-10-10.md`).
- Summarize key facts that will still be true in 3–6 months
  (decisions, tradeoffs, standards, new conventions).

---

## 2. Closure Checklist

- [ ] All pre-commit hooks pass (`make pre-commit`).
- [ ] Branch merged or PR opened.
- [ ] Context delta appended and validated (`python3 scripts/validate_context_delta.py`).
- [ ] Artifacts reviewed (`artifacts/*.json`, logs).
- [ ] Docker containers stopped if no further work is planned (`docker compose down`).

---

## 3. Developer Log Template

```

# Developer Log — <DATE>

## Summary

<Describe what was completed and why it matters.>

## Decisions

* …

## Risks / Issues

* …

## Next Steps

* …

```

---

## 4. Wrap-Up Tasks

1. Commit and push updates:

   ```bash
   git add docs/context docs/dev-logs runbooks
   git commit -m "chore: close session and append context delta"
   git push
   ```

2. Tag session if significant progress was made:

   ```bash
   git tag -a v0.X.Y -m "Session milestone"
   git push origin v0.X.Y
   ```

3. Capture closure summary into the next session kickoff prompt.

---

## 5. References

- `scripts/append_context_delta.sh`
- `scripts/validate_context_delta.py`
- `docs/context/context_delta.log.yaml`
- `runbooks/session_kickoff.md`
