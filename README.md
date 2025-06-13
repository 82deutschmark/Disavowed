# Espionage CYOA Game

A choose-your-own-adventure espionage game with OpenAI-generated storylines and a 4-tier choice system.

## Features

- **4-Tier Choice System**: 3 AI-generated choices with currency costs + 1 custom diamond choice
- **Character Integration**: Choices incorporate random characters from the database as allies/contacts
- **Currency System**: Multi-currency economy (diamonds, dollars, pounds, euros, yen)
- **Dynamic Story Generation**: OpenAI gpt-4.1-nano-2025-04-14 creates mission briefings and story continuations

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
2. Provide OPENAI_API_KEY for story generation
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