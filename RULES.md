# Repository Rules (Maintenance Contract)

This file defines the development contract for this repo. These rules are enforced by review and CI.

## Branching
- One branch per task or ticket.
- Branch naming: task-XX-<short-slug> (or a clear feature/fix name).

## Commits
- Commit only when files have changed.
- Empty commits are not allowed.
- Keep commits scoped to the task and avoid unrelated file changes.

## Required checks
Run these before pushing (or ensure CI runs them):

1) Full test suite
```powershell
python -m pytest -q
```

2) Ruff lint
Run on changed files or scoped targets to avoid legacy debt:
```powershell
python -m ruff check <changed files>
# or
python -m ruff check agent tests
```

3) Mypy (non-blocking)
Mypy runs for signal only and does not gate merges yet because of legacy typing debt. The config uses `ignore_errors = True` and scopes to maintained code.
```powershell
python -X utf8 -m mypy . --show-error-codes
```

## Documentation updates
If behavior, outputs, or usage changes, update the most relevant doc:
- `README.md`
- `QUICK_REFERENCE.md`
- `ARCHITECTURE.md`
- `TROUBLESHOOTING.md`

Keep doc edits minimal and focused on the change.
