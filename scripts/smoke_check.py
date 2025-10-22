import os
import sys
import traceback
from dotenv import load_dotenv


def section(title: str):
    print(f"\n=== {title} ===")


def fail(msg: str, exc: Exception | None = None, exit_code: int = 1):
    print(f"[FAIL] {msg}")
    if exc:
        print(f"Error: {exc}")
        traceback.print_exc()
    sys.exit(exit_code)


def pass_msg(msg: str):
    print(f"[OK] {msg}")


def main():
    section("Load environment")
    load_dotenv()

    required_vars = [
        "SQLALCHEMY_DATABASE_URI",
        "OPENAI_API_KEY",
    ]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        fail(f"Missing required env vars: {', '.join(missing)}")
    pass_msg(".env loaded and required vars present")

    section("DB connectivity: SQLAlchemy engine + SELECT 1")
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(os.environ["SQLALCHEMY_DATABASE_URI"], pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.scalar()
            assert row == 1
        pass_msg("Engine connect and SELECT 1 succeeded")
    except Exception as e:
        fail("Database engine connection failed", e)

    section("DB connectivity: Flask app session query")
    try:
        from app import app, db
        from models import StoryGeneration

        with app.app_context():
            _ = db.session.execute(db.text("SELECT current_database()"))
        pass_msg("Flask app DB session usable")
    except Exception as e:
        fail("Flask app DB session check failed", e)

    section("OpenAI API key validation")
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        models = client.models.list()
        _ = getattr(models, "data", None)
        pass_msg("OpenAI authentication succeeded (models.list)")
    except Exception as e:
        fail("OpenAI authentication failed", e)

    print("\nAll smoke checks passed.")


if __name__ == "__main__":
    main()

