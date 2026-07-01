# AGENTS.md Update Plan

Approved by user. Apply these 2 edits to `/home/jwackito/data/analysis/git/evvents/AGENTS.md`:

---

## Edit 1: Add work tracker convention rule

Replace lines 112-116:

```markdown
## Documentation

- **README.md**: Setup instructions, prerequisites, configuration, how to run (dev + production), project overview.
- **OpenAPI**: Auto-generated from code (apiflask). Serve at `/api/v1/docs/` in development.
- **Inline comments**: Minimal. Only document *why* something is done a certain way, not *what* the code does (the code itself should be clear).
```

With:

```markdown
## Documentation

- **README.md**: Setup instructions, prerequisites, configuration, how to run (dev + production), project overview.
- **OpenAPI**: Auto-generated from code (apiflask). Serve at `/api/v1/docs/` in development.
- **Inline comments**: Minimal. Only document *why* something is done a certain way, not *what* the code does (the code itself should be clear).
- **Work Tracker**: Update the Remaining Work Tracker in AGENTS.md immediately after every completed task. Add new entries to "Recently Completed" (newest first). Verify Backlog items reflect current reality before starting the next task.
```

---

## Edit 2: Update Recently Completed

Replace lines 144-153:

```markdown
### Recently Completed

- **`feat: add plugin base classes with hook interfaces`**
- **`feat: add plugin registry with type-based querying`**
- **`feat: add plugin discovery via importlib.metadata entry points`**
- **`feat: wire plugin system into app factory`**
- **`test: add 16 tests for plugin system`**
- **`feat: implement check-in blueprint with 6 endpoints`**
- **`feat: add check-in service with scan, undo, history, search, stats`**
- *(reset at project start; oldest items drop as new ones are added)*
```

With:

```markdown
### Recently Completed

- **`refactor: use factory_boy for test fixtures`**
- **`feat: add plugin base classes with hook interfaces`**
- **`feat: add plugin registry with type-based querying`**
- **`feat: add plugin discovery via importlib.metadata entry points`**
- **`feat: wire plugin system into app factory`**
- **`test: add 16 tests for plugin system`**
- **`feat: implement check-in blueprint with 6 endpoints`**
- *(reset at project start; oldest items drop as new ones are added)*
```
