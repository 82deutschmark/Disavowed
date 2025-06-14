# Dynamic OpenAI Prompt & DB Alignment Plan

*Author: Cascade*
*Date: 2025-06-14*

---

## 1. Objective
Design and implement a **dynamic, schema-aware prompt workflow** that ensures OpenAI responses
1. Only include information required by the database schema (`story_generation`, `story_node`, `mission`).
2. Respect existing field length constraints (e.g. `VARCHAR(255)` limits).
3. Remain flexible so future schema changes can be accommodated with minimal code changes.

## 2. Scope & Approach
1. **Schema Audit**
   * Extract max lengths & datatypes for all story-related tables.
   * Identify mandatory vs optional fields.
2. **Prompt Template Redesign**
   * Create parameterised prompt strings for:
     * `generate_full_mission_story`
     * `generate_story_continuation`
     * `generate_choices`
   * Enforce a compact JSON response containing ONLY the following keys:
     ```json
     {
       "mission_title": "string <=200",
       "mission_description": "text (~1-2 paragraphs)",
       "objective": "text <=255",
       "difficulty": "enum(low|medium|high)",
       "deadline": "string <=200",
       "setting": "string <=500",
       "narrative_style": "string <=100",
       "mood": "string <=100",
       "opening_narrative": "text (~2-3 short paragraphs, <2k chars)",
       "choices": [{"text": "<=255", "character_used": "string", "risk_level": "enum"}]
     }
     ```
   * Provide guidelines inside the prompt to **hard-stop** at token/char budgets.
3. **Safe Parsing Layer**
   * Create helper `def safe_json_parse(raw_str)` inside `openai_integration.py` to:
     * Parse JSON, validate key presence, truncate over-length values, and log warnings.
4. **Game Engine Updates**
   * Modify `GameEngine.create_full_mission` to use the parsed object and map fields directly to `Mission`, `StoryGeneration`, `StoryNode`.
5. **Validation & Testing**
   * Add unit tests validating:
     * Prompt returns parsable JSON.
     * All string lengths ≤ DB limits.
     * End-to-end mission creation succeeds without `value too long` errors.

## 3. Deliverables
- Updated **`openai_integration.py`** with new prompt templates & parsing utilities.
- Updated **`game_engine.py`** with schema-aware storage logic.
- New **unit tests** under `tests/`.
- Updated documentation:
  * `docs/game_flow_and_prompt_design.md` (prompt details)
  * `CHANGELOG.md` (summary of changes with timestamp)

## 4. File Impact
### To Modify
- `openai_integration.py`
- `game_engine.py`
- `routes.py` (only if parameter flow needs adjustment)
- `docs/game_flow_and_prompt_design.md`
- `CHANGELOG.md`

### To Create
- `tests/test_prompt_alignment.py`
- (this) `docs/dynamic_prompt_db_alignment_plan.md`

## 5. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| OpenAI response exceeds limits | DB write failure | Hard character caps + truncation in `safe_json_parse` |
| Schema changes later | Prompt/parse mis-match | Centralise field map constants for easy update |
| JSON parse errors | Runtime failure | Retry logic + fall-back minimal story |

## 6. Timeline (Effort ≈ 6-8 hrs development)
1.  **0.5 hr** – Schema audit & constant definition
2.  **1.0 hr** – Prompt template drafting & iteration
3.  **2.0 hr** – `openai_integration.py` refactor (templates + parser)
4.  **1.5 hr** – `game_engine.py` adjustments & integration test
5.  **1.0 hr** – Unit tests & docs updates
6.  **0.5 hr** – Review & polish

## 7. Checklist
- [ ] Audit schema & capture limits
- [ ] Draft & finalise new prompt templates
- [ ] Implement `safe_json_parse`
- [ ] Integrate parsing into mission creation flow
- [ ] Create / update unit tests
- [ ] Update documentation & changelog
- [ ] Manual QA: create mission end-to-end without DB errors

---
**Please review this plan and provide approval or adjustments before I proceed with implementation.**
