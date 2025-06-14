# Disavowed Changelog

_All notable changes to the project will be documented in this file._

---

## [2025-06-13] - Added Hero Image to Landing Page

* Incorporated `static/images/Disavowed.png` into `templates/index.html` hero section.
* Updated `README.md` feature list to mention new key art landing image.
* Created `static/images` directory and copied image asset.
* This entry authored automatically by **Cascade**.

---

## [2025-06-14] - Local Development Support & Dependency Update

* Added `LOCAL_DOMAIN` variable to `.env` for running outside Replit.
* Refactored `google_auth.py` and `stripe_payments.py` to fall back to `LOCAL_DOMAIN` when `REPLIT_DEV_DOMAIN` is absent.
* Added `python-dotenv` to `requirements.txt` so environment variables load automatically when running locally.
* Updated documentation regarding Google OAuth redirect URI instructions.
* This entry authored automatically by **Cascade**.
