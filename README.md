### Context log

- Append with: `./scripts/append_context_delta.sh < my_delta.yaml`
- Validate with: `python3 scripts/validate_context_delta.py`
- One-shot test: `make test-log` (appends one valid entry, then demonstrates a failing append)
