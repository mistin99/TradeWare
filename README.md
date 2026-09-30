# TradeWare

TradeWare is a FastAPI backend. This README covers local setup, the current
registration and email-verification flow, and the database migration status.

## Requirements

- Python 3.10 or newer
- PostgreSQL for persistent local or deployed use, or Docker Compose

## Local setup

Create and activate a virtual environment, then install the project and its
development tools:

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and set the database values. For a locally
installed PostgreSQL server, use `DATABASE_HOST=localhost`. For the Compose
database, the application container uses `DATABASE_HOST=db`; the host machine
connects to the published database at `localhost:5432`.

Run the application with:

```bash
python -m uvicorn trade_ware.main:app --reload
```

The API is available at `http://localhost:8000`

## Docker Compose

After setting the values in `.env`, build and start the services:

```bash
docker compose up --build
```

The API is published on port `8000`, PostgreSQL on `5432`, and the development
debugger on `5678`. The debugger waits for a VS Code attach session as configured
in `.vscode/launch.json` before the API starts. Do not expose the debugger port
outside local development.

## Authentication and email verification

Authentication endpoints are currently under `/api/v1/auth`:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Register an account and send a verification email |
| `GET` | `/api/v1/auth/verify-email?token=...` | Verify an account using its one-time token |

Registration accepts JSON containing an email address and a password of at
least eight characters. The email is normalized to lowercase. The password is
stored as a salted hash; the original password is not stored.

Registration creates a user with `is_verified=false` and a separate
`email_verification_tokens` record. The verification link is sent to the
registered address. A successful verification sets `is_verified=true` and
deletes that token, so it cannot be reused. The registration response currently
also includes the verification URL, which is useful for local development.
Verification tokens are valid for 15 minutes. An expired token is rejected and
deleted when it is used. Registration also opportunistically deletes expired
tokens, so stale rows are cleaned up as new accounts register; a scheduled
cleanup task can be added if token volume later requires more frequent purging.

The verification URL is built from `APP_BASE_URL`. Set it to the address users
can reach (for example, `http://localhost:8000` during local development). The
SMTP settings (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, and `SMTP_PASSWORD`)
are loaded from `.env`. If SMTP is not configured, the email service logs the
message for development instead of connecting to a mail server. The current
sender address is the authenticated `SMTP_USERNAME`.

## Database initialization and migrations

At application startup, SQLAlchemy `Base.metadata.create_all()` creates tables
that do not exist. It does **not** update existing tables when columns,
constraints, or types change. It is adequate for the current initial schema,
but it is not a schema migration strategy and cannot guarantee safe upgrades.

## Tests

Tests are grouped alongside their modules under `src/trade_ware/**/tests/`.
Email behavior is mocked in unit tests, so tests do not send real messages.
