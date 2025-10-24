# Disavowed knowledge

- Purpose: Flask-based espionage CYOA game with OpenAI-driven narrative and PostgreSQL.
- Run locally: `python main.py` (http://localhost:5000)
- Prod (per README): `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`
- Key env vars: OPENAI_API_KEY (required), SESSION_SECRET (optional), DATABASE_URL (if overriding), Stripe/Google OAuth if enabled.
- Tech: Flask, SQLAlchemy, Flask-Login, OpenAI SDK, Stripe.
- Notes:
  - Game flow: start_game -> mission generation -> game loop with AI-generated choices.
  - DB: Postgres (Neon). Models defined in models.py; tables auto-created at app startup.
  - Static assets in static/, Jinja templates in templates/.
- Codebuff:
  - Background process configured: Flask dev server via `python main.py` (logs/flask.log)
  - No fileChangeHooks configured yet.
