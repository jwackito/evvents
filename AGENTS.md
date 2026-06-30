# Evvents — Engineering Conventions

## Python

- **Style**: PEP 8. Use `black` (88 char line length) + `isort` + `ruff` for linting.
- **Type hints**: Required on all function signatures. Use `from __future__ import annotations` for cleaner syntax.
- **Strings**: f-strings always. Never `.format()` or `%` formatting.
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants.
- **Imports**: grouped: standard library → third-party → local. Sort alphabetically within groups.
- **Error handling**: Define custom exception classes in `app/exceptions.py`. Never `raise Exception("...")`. Catch specific exceptions, never bare `except:`.
- **Logging**: Use `structlog` (structured JSON logs). Log at appropriate levels: `debug` for dev details, `info` for normal operations, `warning` for recoverable issues, `error` for failures.
- **Config**: Environment variables via `pydantic-settings` or `python-decouple`. Never hardcode secrets, URLs, or environment-specific values.

## Flask

- **App factory**: `create_app()` in `app/__init__.py`. No global app instance.
- **Blueprints**: One blueprint per domain area: `auth`, `events`, `tickets`, `checkin`, `admin`, `bot`.
- **Separation**: Routes (blueprints) only parse request/response. Business logic lives in `app/services/`. Database access lives in models or service layer.
- **Validation**: Use `marshmallow` or `pydantic` schemas for request validation. Never trust raw `request.json`.
- **Error responses**: All errors return consistent JSON: `{"error": "message", "code": "ERROR_CODE"}`. Use Flask error handlers registered in the app factory.

## API Design

- **Naming**: RESTful resource nouns (`/events`, `/tickets`, `/orders`). No verbs in URLs.
- **Versioning**: Prefix all routes with `/api/v1/`.
- **Pluralization**: Collections are plural (`GET /events`, `POST /tickets`). Single resource: `GET /events/<id>`.
- **Pagination**: Query params `?page=1&per_page=20`. Response includes `{ "data": [...], "total": N, "page": N, "per_page": N }`.
- **Status codes**: 200 (success), 201 (created), 204 (deleted), 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 409 (conflict), 422 (validation error), 500 (server error).
- **Consistent response shape**:
  - Single: `{ "data": { ... } }`
  - List: `{ "data": [...], "total": N, "page": N, "per_page": N }`
  - Error: `{ "error": "message", "code": "ERROR_CODE", "details": {} }`
- **OpenAPI**: Document all endpoints with Apiflask or flask-smorest. Keep spec in sync with code.

## Database

- **Migrations**: Alembic. Every schema change is a new migration. Never edit existing migrations after they're committed.
- **Timestamps**: All tables get `created_at` (UTC, auto-set) and `updated_at` (UTC, auto-update).
- **Soft deletes**: Use `deleted_at` timestamp column for entities where data integrity matters (events, orders). Hard delete only for truly ephemeral data.
- **Indexes**: Index foreign keys, columns used in `WHERE`/`ORDER BY`, and columns used in lookups (`slug`, `email`, `telegram_chat_id`).
- **Queries**: Write raw SQL only when ORM can't express the query efficiently. Prefer SQLAlchemy ORM for 90% of queries.
- **Naming**: Tables are `snake_case` plural (`events`, `ticket_types`). Primary key always `id`. Foreign keys: `{table}_id` (e.g., `organization_id`).

## Models (SQLAlchemy)

- **Declarative base**: All models inherit from a common `Base` class in `app/extensions.py`.
- **Mixin**: Use a `TimestampMixin` for `created_at`/`updated_at` and `SoftDeleteMixin` for soft deletes.
- **Relationships**: Define `back_populates` explicitly on both sides. Use `lazy="selectin"` for small-to-medium relationships, `lazy="dynamic"` for large collections.
- **Validation**: Keep it in the service layer, not in models. Models are data containers.

## React / TypeScript

- **Components**: Functional components with hooks. No class components.
- **TypeScript**: `strict: true` in tsconfig. Define interfaces for all props, API responses, and state shapes.
- **Naming**: `PascalCase` for components and types, `camelCase` for variables/functions/hooks, `SCREAMING_SNAKE` for constants.
- **File per component**: One component per file, named after the component.
- **Hooks**: Custom hooks for data fetching (`useEvents`, `useTickets`), local state abstraction, and reusable logic.
- **State management**: Zustand for global state (auth, current org). React Query (TanStack Query) for server state (caching, refetching, mutations).
- **Styling**: Use a consistent approach (CSS Modules or Tailwind). Keep styles co-located with components.
- **API calls**: Centralized API client in `src/services/api.ts` with interceptors for auth token injection and error handling.
- **Routing**: React Router v6. Lazy-load route pages.

## Testing

- **Framework**: pytest for backend, Vitest + React Testing Library for frontend.
- **Coverage**: Aim for 80%+ on backend services and API endpoints. Frontend: test critical user flows.
- **Fixtures**: Use pytest fixtures for database session, test client, and sample data. Use `factory_boy` for model factories.
- **Test structure**: Mirror the source structure: `tests/api/`, `tests/services/`, `tests/models/`.
- **Naming**: `test_{function_name}_{scenario}` for unit tests. `test_{endpoint}_{scenario}` for API tests.
- **What to test**:
  - Services: business logic, edge cases, error conditions
  - API: status codes, response shape, auth enforcement, validation errors
  - Models: constraints, relationships, custom methods
  - Frontend: component rendering, user interactions, API integration
- **What NOT to test**: Third-party library behavior, trivial getters/setters, Flask/SQLAlchemy internals.

## Git

- **Conventional commits**: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`, `style:`, `perf:`, `ci:`, `build:`. Example: `feat: add Telegram ticket card sending`
- **Branching**: Feature branches from `main`. Name: `feat/description`, `fix/description`, `chore/description`.
- **Commits**: Small, focused, one logical change per commit. Write descriptive commit messages (imperative mood).
- **Merging**: Squash merge feature branches into `main`. Keep `main` history linear and clean.
- **Before commit**: Run linter + tests locally. Never commit broken code.

## Docker

- **Multi-stage builds**: Separate build and runtime stages to minimize image size.
- **Non-root user**: Run containers as a non-root user. Never run as root.
- **Health checks**: Define `HEALTHCHECK` for each service.
- **Service dependencies**: Use `depends_on` in docker-compose. Wait for PostgreSQL and Redis to be ready before starting the API.
- **Volumes**: Named volumes for database data and uploaded files. Bind mounts for development hot-reload.
- **Environment**: `.env` file for local dev, environment variables for production. Never commit `.env` to git.

## Security

- **Secrets**: Never hardcode secrets, API keys, or tokens. Use environment variables or Docker secrets.
- **Input validation**: Validate and sanitize all user input. Use marshmallow/pydantic schemas.
- **SQL injection**: Prevented by SQLAlchemy's parameterized queries. Never use raw string interpolation in SQL.
- **Auth tokens**: JWT with short expiry (15 min access, 7 day refresh). Store refresh tokens in HTTP-only cookies.
- **Rate limiting**: Apply to auth endpoints (login, magic link) to prevent brute force. Use Flask-Limiter.
- **CORS**: Restrict to known origins in production. Allow all origins only in development.
- **CSRF**: API uses token-based auth (JWT), so CSRF is not applicable. For any cookie-based auth, implement CSRF tokens.
- **Helmet**: Set secure HTTP headers (via Flask-Talisman or similar).

## Error Handling & Logging

- **Structured logging**: All logs are JSON. Include: `timestamp`, `level`, `logger`, `message`, `request_id`, `user_id`, `organization_id`.
- **Request ID**: Generate a unique ID per request (UUID). Pass it to background jobs for traceability.
- **Error boundaries**: Flask error handlers for 400, 401, 403, 404, 405, 422, 500. Never leak stack traces in production.
- **Background jobs**: Log job start/end/duration. Retry failed jobs with exponential backoff (max 3 retries). Dead-letter queue after max retries.

## Documentation

- **README.md**: Setup instructions, prerequisites, configuration, how to run (dev + production), project overview.
- **OpenAPI**: Auto-generated from code (apiflask). Serve at `/api/v1/docs/` in development.
- **Inline comments**: Minimal. Only document *why* something is done a certain way, not *what* the code does (the code itself should be clear).

## Scope of Authority

- **Project only**: All modifications are restricted to files within the project directory.
- **Never modified**: System configs, global packages, home directory files, or anything outside the project. If an external change is needed (e.g., system dependency), explicit permission is requested first.

## Remaining Work Tracker

This section is updated after every completed task and when new features are requested. Items are sorted by priority within each category.

### Backlog

#### Low Effort / High Value
- [ ] **Wire `enqueue_ticket_card` to order creation** — call from `POST /events/<slug>/order` so ticket cards auto-send on purchase. *(1 file, ~2 lines)*
- [ ] **Docker `HEALTHCHECK`** — add to `Dockerfile` `production` stage. *(1 line)*
- [ ] **Init flask-cors** — call `CORS(app)` in `create_app()`. *(1 line)*

#### Features
- [ ] **Check-in blueprint** — `app/api/checkin.py` is empty; needs real endpoints (scanning, validation, history).
- [ ] **Plugin system** — `app/plugins/__init__.py` is empty; `pyproject.toml` has entry-point stubs.

#### Testing
- [ ] **Unit tests for services** — `email_service`, `order_service`, `waitlist_service`, `seating_service`, `admin_service`.
- [ ] **Unit tests for tasks** — `telegram_tasks`, `email_tasks`.
- [ ] **Unit tests for utils** — JWT utils, decorators.
- [ ] **Unit tests for models** — constraints, relationships, custom methods.

#### Frontend
- [ ] **Scaffold React SPA** — Vite + TypeScript + React Router + Zustand + TanStack Query. No code exists.

### Recently Completed

- *(reset at project start; oldest items drop as new ones are added)*
