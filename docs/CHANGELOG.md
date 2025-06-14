<!-- Updated by o3-high reasoning on 2025-06-14 -->
# Disavowed Changelog

_All notable changes to the project will be documented in this file._

---

## [2025-06-14] - Dynamic Prompt Database Alignment Implementation

* **Major System Enhancement**: Implemented schema-aware prompt templates and safe JSON parsing throughout OpenAI integration.
* **Database Field Validation**: Added automatic field length validation and truncation to prevent "value too long" database errors.
* **Structured AI Responses**: Updated all OpenAI integration functions to return validated JSON with specific field mappings.
* **Enhanced Error Handling**: Improved error logging and fallback mechanisms for AI generation failures.
* **Variable Name Consistency**: Fixed critical variable naming inconsistencies in prompt construction and data handling.
* **Game Engine Integration**: Updated game engine to properly handle structured JSON responses from AI functions.
* **Schema Constraints**: Added database schema limit definitions to ensure AI responses fit within field constraints.
* **Safe Parsing Layer**: Implemented `safe_json_parse()` function with markdown cleanup and recursive field validation.
* **Prompt Template Redesign**: Created parameterized prompt strings with strict field length enforcement for mission generation, story continuation, and choice generation.
* This comprehensive update ensures reliable AI-to-database integration and eliminates data overflow errors.
* This entry authored automatically by **Cascade** - 2025-06-14T23:28:00Z.

---

## [2025-06-14] - Local Development Support & Dependency Update

* Added `LOCAL_DOMAIN` variable to `.env` for running outside Replit.
* Refactored `google_auth.py` and `stripe_payments.py` to fall back to `LOCAL_DOMAIN` when `REPLIT_DEV_DOMAIN` is absent.
* Added `python-dotenv` to `requirements.txt` so environment variables load automatically when running locally.
* Updated documentation regarding Google OAuth redirect URI instructions.
* This entry authored automatically by **Cascade**.

---

## [2025-06-14] - README Alignment with Game Concept & Schema

* Expanded `README.md` with detailed game concept, mission structure, core mechanics, and full database overview.
* Added author attribution comment at the top of `README.md` with timestamp.
* Documentation now accurately reflects information from Game Concept Overview and Database Schema Documentation.
* This entry authored automatically by **o3-high reasoning**.

---

## [2025-06-14 18:43] - Schema Validation Fix & JSON Handling Simplification
**Author: Cascade**

### Fixed
- **Database constraint violations**: Fixed schema validation that was allowing fields longer than database limits
- **Schema limits alignment**: Corrected `setting` field limit from 500 to 255 characters to match database constraints
- **JSON parsing logic**: Simplified parsing since OpenAI already returns valid JSON with `response_format={"type": "json_object"}`
- **Validation logic**: Improved recursive validation to properly handle nested structures like `choices` arrays

### Technical Details
- The root issue was that OpenAI responses contained fields longer than database VARCHAR limits
- Schema validation wasn't properly truncating fields before database insertion
- Removed unnecessary manual JSON parsing complexity since OpenAI guarantees valid JSON
- This fixes the "value too long for type character varying(255)" database errors

### Impact
- Mission creation should now work without database constraint violations
- Cleaner, more reliable OpenAI integration
- Better alignment between AI responses and database schema requirements

---

## [2025-06-13] - Added Hero Image to Landing Page

* Incorporated `static/images/Disavowed.png` into `templates/index.html` hero section.
* Updated `README.md` feature list to mention new key art landing image.
* Created `static/images` directory and copied image asset.
* This entry authored automatically by **Cascade**.
