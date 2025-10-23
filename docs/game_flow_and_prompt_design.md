# Game Flow and Prompt Design Blueprint

**Author:** Cascade
**Date:** 2025-06-14

## 1. Overview

This document outlines the core data and logic flow for the Disavowed game engine, from initial mission creation to the turn-by-turn gameplay loop. It details how the application interacts with the database and the OpenAI Responses API to create a dynamic, coherent narrative experience. This blueprint will guide the necessary code changes to fix the current database errors and streamline the story generation process.

### 1.1 Responses API Modernization

The codebase now routes all narrative generation through a single `OpenAIIntegration` helper that calls `client.responses.create(...)` (or the streaming variant) with split **instructions** and **input** payloads. The helper exposes:

* Shared defaults for the text model (`gpt-5-nano` by default) and temperature/max token budgets.
* `response_format={"type": "json_object"}` enforcement so we receive schema-compliant JSON without manual role parsing.
* Optional streaming generators that yield `delta` chunks while keeping a final validated JSON payload for downstream consumers.

Any future feature work should reuse these helpers instead of crafting raw prompts.

## 2. The "Jet Engine" Analogy: Two-Phase Generation

To use the user's analogy, our game engine operates in two distinct phases, each requiring a different "fuel mixture" (i.e., a different type of AI prompt).

*   **Phase 1: The Startup Sequence (Mission Generation)**: This is a one-time, high-powered process to create the mission's foundation. It's like turning the choke up on an engine to get it started.
*   **Phase 2: The Running Engine (Gameplay Loop)**: This is an efficient, iterative process that generates the story turn-by-turn as the player makes choices. It's the engine running smoothly at cruising speed.

---

## 3. Phase 1: The Startup Sequence (Mission Generation)

This phase creates the `StoryGeneration` record and the very first `StoryNode`.

**Trigger:** The user creates their characters and clicks "Begin Mission" in the `mission_assignment.html` view.

**Process Flow:**

1.  **Route (`/start_game`)**: The Flask route receives the selected character IDs.
2.  **Game Engine (`create_full_mission`)**: This function is called with the character information.
3.  **OpenAI Integration (`generate_full_mission_story`)**: This function constructs and sends the **Initial Prompt** to the OpenAI Responses API via the shared helper (instructions text + input payload).

**The Initial Prompt ("Rich Fuel Mix")**

This is a detailed prompt designed to generate a complete mission context. 

*   **Inputs (The "Fuel")**:
    *   Selected Character IDs and their descriptions/backgrounds from the `Character` table.
    *   High-level scenario parameters (e.g., "An infiltration mission in a high-tech lab").
*   **Instructions (The "Engine Order")**:
The helper provides a reusable instructions string ("You are a professional game narrative designer...") and appends call-specific rules. The `response_format={"type": "json_object"}` flag ensures the OpenAI service enforces the JSON schema at generation time, eliminating the need for role-based message parsing.

*   **Proposed JSON Output from AI:**
    ```json
    {
      "story_generation": {
        "primary_conflict": "A short, actionable summary of the main mission goal (e.g., 'Steal the Project Chimera prototype before it's sold to the highest bidder').",
        "setting": "A concise description of the overall mission setting (e.g., 'A lavish, high-security casino in Monaco during a charity gala').",
        "narrative_style": "(Can be selected by user) Default is 'Modern Espionage Thriller'",
        "mood": "(Can be selected by user) Default is 'Action-packed and Suspenseful'"
      },
      "initial_story_node": {
        "narrative_text": "The first scene's descriptive text, setting the stage for the player.",
        "choices": [
          {"text": "Choice 1 description", "next_node_summary": "A brief for the AI on what happens if this is chosen"},
          {"text": "Choice 2 description", "next_node_summary": "A brief for the AI on what happens if this is chosen"},
          {"text": "Choice 3 description", "next_node_summary": "A brief for the AI on what happens if this is chosen"}
          {"text": "User input", "next_node_summary": "AI should consider {user input} for story development"}
        ]
      }
    }
    ```

**Database Action:**

1.  A single new record is created in the `StoryGeneration` table using the data from the `story_generation` part of the AI's response.
2.  A single new record is created in the `StoryNode` table. This is the root node of the mission's story tree. Its `narrative_text` and choice data come from the `initial_story_node` part of the response.

**Result:** The user is presented with the `game.html` view, displaying the `narrative_text` and choices from this first `StoryNode`.

---

## 4. Phase 2: The Running Engine (Gameplay Loop)

This phase generates subsequent `StoryNode` records each time the player makes a choice.

**Trigger:** The user clicks a choice button in the `game.html` view.

**Process Flow:**

1.  **AJAX/Fetch Call**: The browser sends the ID of the current `StoryNode` and the chosen option to a new backend route (e.g., `/make_choice`). (We can optionally adopt streaming here by calling the helper with `stream=True` and piping deltas to the client.)
2.  **Route (`/make_choice`)**: The route retrieves the relevant data.
3.  **Game Engine (`generate_next_node`)**: A new function will be created for this.
4.  **OpenAI Integration (`generate_next_story_node`)**: This function constructs and sends the **Continuing Prompt**.

**The Continuing Prompt ("Lean Fuel Mix")**

This prompt is much smaller and more focused. Its job is to maintain story coherence.

*   **Inputs (The "Fuel")**:
    *   `primary_conflict` from the parent `StoryGeneration` record (to keep the AI on-mission).
    *   `narrative_text` from the parent `StoryNode` (to give immediate context).
    *   The text of the choice the player just made (e.g., `next_node_summary` from the parent's choice data).
*   **Instructions (The "Engine Order")**:
The prompt asks the AI to generate the outcome of the chosen action and leverages the same Responses API helper. By passing `stream=True` we can progressively send narrative text to the UI while still validating the final JSON payload once the stream completes.

*   **Proposed JSON Output from AI:**
    ```json
    {
      "narrative_text": "The text for the new scene, describing the outcome of the player's choice.",
      "choices": [
          {"text": "New Choice 1", "next_node_summary": "..."},
          {"text": "New Choice 2", "next_node_summary": "..."}
          {"text": "New Choice 3", "next_node_summary": "..."}
          {"text": "User input", "next_node_summary": "..."}
      ]
    }
    ```

**Database Action:**

1.  A new `StoryNode` record is created. Its `parent_node_id` is set to the ID of the node the player was just on. This is how we build the story tree.

**Result:** The `game.html` view is dynamically updated with the new `narrative_text` and choices, without a full page reload.

## 5. Implementation Plan

-   [ ] **Modify `openai_integration.py`**: Create two distinct functions, `generate_full_mission_story` and `generate_next_story_node`, with the new prompt structures.
-   [ ] **Modify `game_engine.py`**: 
    -   Update `create_full_mission` to handle the new JSON structure from the AI and correctly populate the `StoryGeneration` and initial `StoryNode` tables.
    -   Create a new function `generate_next_node` to manage the gameplay loop.
-   [ ] **Modify `routes.py`**:
    -   Update the `/start_game` route logic.
    -   Create a new `/make_choice` route to handle player actions during the game.
-   [ ] **Update `game.html`**: Implement AJAX/Fetch calls to the `/make_choice` endpoint to create a seamless, dynamic gameplay experience.
-   [ ] **Update `Changelog.md` and `README.md`** with all changes.
