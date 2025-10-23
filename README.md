<!-- Updated by o3-high reasoning on 2025-06-14 -->
# Espionage CYOA Game `Disavowed`

A choose-your-own-adventure espionage game with OpenAI-generated storylines and a 4-tier choice system.

## Features

- **Key Art Landing Image**: Visually striking hero image added to landing page (static/images/Disavowed.png)

- **4-Tier Choice System**: 3 AI-generated choices with currency costs + 1 custom diamond choice
- **Character Integration**: Choices incorporate random characters from the database as allies/contacts
- **Currency System**: Multi-currency economy (diamonds, dollars, pounds, euros, yen)
- **Dynamic Story Generation**: OpenAI's Responses API (default `gpt-5-nano` model) powers mission briefings and story continuations with structured JSON guarantees
- **Progressive Streaming**: Long-form mission intros and narrative beats can stream token-by-token to the UI for faster feedback

## Architecture

- **Flask** web application with PostgreSQL database
- **OpenAI Integration** for dynamic content generation
- **Game Engine** handles choice processing and currency management
- **Character Database** contains pre-existing characters for story integration

## Database Tables

- `characters` - Character profiles with traits and backstories
- `story_node` - Individual story segments
- `story_choice` - Available choices at each story node
- `user_progress` - Player state and currency balances
- `mission` - Active player missions
- `transaction` - Currency transaction history

## Setup

1. Ensure PostgreSQL database is configured with DATABASE_URL
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Provide OPENAI_API_KEY for story generation (optional `OPENAI_TEXT_MODEL` overrides the default `gpt-5-nano`)
3. Run with: `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`

## Game Flow

1. Player starts and receives mission assignment from character from the database with the role of "mission-giver"
2. OpenAI generates opening story narrative
3. Engine creates 3 AI choices (each featuring different random characters) + 1 custom option
4. Player selections advance story with currency costs
5. Continuous story generation based on player choices

## Currency Costs

- Low tier: 💵5, 💷4, 💶4, 💴50
- Medium tier: 💵15, 💷12, 💶13, 💴150  
- High tier: 💵25, 💷20, 💶22, 💴250
- Diamond choice: 💎1 (custom player input)

## Game Concept

**Genre:** Interactive narrative adventure (choose-your-own-adventure)

**Premise:** You play a rogue agent recently *disavowed* by their spy agency. With limited diamonds and other currencies, you undertake high-risk missions assigned by dynamically selected characters from the database.

### Theme & Player Role
* Irreverent espionage with bold, risk-taking attitude.
* Think "Rick Sanchez" from *Rick and Morty* meets Sterling Archer from *Archer*.
* Navigate chaotic missions rife with unpredictable twists.

### Mission Structure
1. Receive a mission briefing from a mission-giver (`Character` role="mission-giver").
2. Narrative unfolds through sequential `StoryNode` decisions.
   * **Low-cost choices** (💵/💴/💶/💷) introduce surprise characters and flavourful events.
   * **High-cost choices** (💎) branch the story toward mission success or failure.

### Core Mechanics
* **Dual-Tier Decision System:** Low-cost vs premium diamond choices with differing narrative impact.
* **Currency Management:** Diamonds are scarce and gate critical outcomes; other currencies enhance narrative depth.
* **Dynamic Storytelling:** OpenAI (Responses API) generates fresh narrative content for each choice, bounded by DB field limits and validated automatically. Streaming helpers are available for any future endpoints that need progressive updates.
* **State Machine:** A simplified FSM tracks current `StoryNode`, currency balances, and mission progress.

## Database Overview

Below is the full list of tables with concise purpose statements (see schema docs for details):

| Table | Purpose |
|-------|---------|
| Currency | Defines all in-game currencies & symbols |
| Transaction | Logs every currency spend/earn event |
| Character | Core character profiles inc. traits & roles |
| SceneImages | Metadata for background & setting imagery |
| StoryGeneration | High-level story objects (setting, mood, etc.) |
| StoryNode | Individual narrative nodes within a story |
| StoryChoice | Choices that connect `StoryNode` objects |
| UserProgress | Tracks each player's state, currencies & path |
| CharacterEvolution | Records how characters change per user/story |
| Mission | Dynamically generated missions for players |
| Achievement | Unlockable achievements & rewards |
| PlotArc | Long-form narrative arcs spanning many nodes |
| AIInstruction | Stores AI prompt templates & parameters |

**Key Relationships**
* `StoryGeneration` ↔ `SceneImages` & `Character` (many-to-many)
* `StoryNode` self-references for branching narrative
* `StoryChoice` links nodes and sets currency requirements
* `UserProgress` centralises player state, currency, achievements
* `Mission` ties story context (`StoryGeneration`) to characters

---
*Last updated 2025-06-14 by **o3-high reasoning***