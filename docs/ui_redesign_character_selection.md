# UI Redesign Plan – Character Selection Page

**Author:** Cascade
**Date:** 2025-06-14

## Objective
Redesign `templates/character_selection.html` so that players:
1. Clearly understand THEY are the protagonist.
2. Choose three supporting roles (mission-giver, villain/target, partner) with visual character cards.
3. Select (or override) default `narrative_style` and `mood` text values.
4. Easily locate a prominent **“Start Mission”** button.

## Summary of Changes
| File | Action |
|------|--------|
| `templates/character_selection.html` | Major HTML restructure: responsive Bootstrap grid, image display, collapsible character bios, text inputs for narrative style & mood (with defaults pre-filled), larger primary button. |
| `routes.py` | Update `/start_game` POST handler to receive `narrative_style` and `mood` from form and pass to `GameEngine.create_full_mission`. |
| `game_engine.py` | Pass user-chosen style/mood to `OpenAIIntegration.generate_full_mission_story`. |
| `openai_integration.py` | Include style/mood fields in Initial Prompt JSON spec (already supported by design doc). |
| `templates/start_game.html` (rename suggestion → `mission_loading.html`) | Brief loading screen after form submit (optional). |

## Page Layout Sketch
```
[Heading]  Assemble Your Team, Agent

[Row]
  [Col-md-4]  Mission Giver (RadioGroup)
     └ Card • Image • Name • short desc (collapse: full bio)
  [Col-md-4]  Target / Villain (RadioGroup)
  [Col-md-4]  Partner (RadioGroup)

[Row]  Story Preferences
 ├ Narrative Style: [ text input ]  (placeholder: "Modern Espionage Thriller")
 └ Mood:            [ text input ]  (placeholder: "Action-packed and Suspenseful")

[Center]  [ START MISSION ] (btn-lg btn-success w/ icon)
```

## Checklist
- [ ] Modify template with new Bootstrap structure and image tags (`<img src="{{ giver.image_url }}" …>` etc.).
- [ ] Add `narrative_style` & `mood` inputs (name attributes `narrative_style`, `mood`).
- [ ] Validate defaults on server side if user leaves blank.
- [ ] Update `/start_game` route logic to capture new fields.
- [ ] Propagate through `GameEngine` → `OpenAIIntegration`.
- [ ] Optional: lightweight loading screen between submission and mission assignment.

## Questions for Confirmation
1. Are the default placeholders **Modern Espionage Thriller** & **Action-packed and Suspenseful** acceptable?
2. Is a loading screen desired or can we stay on same page until mission loads?
3. Any branding/style guidelines (fonts, colours) I should follow?

Once confirmed, I will implement the changes in a single commit and update the changelog & README accordingly.
