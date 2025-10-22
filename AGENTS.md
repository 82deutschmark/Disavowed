# Repository Guidelines

## Project Structure & Module Organization
- Python Flask app with SQLAlchemy models and Jinja templates.
- Core modules: `app.py` (Flask/DB init), `routes.py` (views), `models.py` (ORM), `game_engine.py` (logic), `openai_integration.py` (AI), `google_auth.py` (OAuth), `stripe_payments.py` (billing).
- Web assets: `templates/` (HTML), `static/css/`, `static/js/`, `static/images/`.
- Utilities and migrations: `migrate_user_progress.py`, `run_migration.py`, `migration_routes.py`.
- Docs: `docs/`; auxiliary inputs in `attached_assets/`.

## Build, Test, and Development Commands
- Setup (Python 3.11): `python -m venv .venv && .venv\\Scripts\\activate && pip install -r requirements.txt`
- Run (dev): `python main.py` (auto-reload, port 5000)
- Run (prod-like): `gunicorn --bind 0.0.0.0:5000 --reload main:app`
- DB migration (CLI): `python migrate_user_progress.py` or `python run_migration.py`
- DB migration (HTTP): `POST /admin/migration/add_authenticated_user_id`

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indents; snake_case for functions/vars; PascalCase for classes.
- Flask: Keep routes in `routes.py`; blueprint names are lowercase with underscores.
- Templates: Jinja blocks (`base.html`) with descriptive template names; static asset paths under `static/`.
- SQLAlchemy: One model class per table; explicit `__tablename__`; prefer `relationship()` over manual joins.
- Add module/class/function docstrings where behavior isn’t obvious.

## Testing Guidelines
- Framework: pytest (recommended). Place tests in `tests/` with `test_*.py` naming.
- Scope: Unit-test `game_engine.py` logic and model behaviors; prefer app-factory patterns for future Flask testing.
- Run: `pytest -q` (add when tests exist). Aim for coverage on branching logic and currency rules.

## Commit & Pull Request Guidelines
- Commits: Imperative mood, short subject (≤72 chars). Example: `feat(engine): generate tiered choices`.
- PRs: Include purpose, key changes, setup/migration notes, and screenshots for UI routes (`/`, `/game`, `/buy-diamonds`). Link issues and note breaking changes.

## Security & Configuration Tips
- Use a `.env` for secrets (do not commit): `OPENAI_API_KEY`, `SESSION_SECRET`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `STRIPE_SECRET_KEY`, `DATABASE_URL` (or `SQLALCHEMY_DATABASE_URI`), `LOCAL_DOMAIN`.
- Prefer environment-driven DB URIs over hard-coded values; `python-dotenv` is already included.
- Never log API keys or tokens; scrub PII in logs.

