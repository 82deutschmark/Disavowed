import json
import os
import logging
from openai import OpenAI

class OpenAIIntegration:
    """
    Integration with OpenAI for dynamic story generation
    Author: Cascade
    
    This module handles all OpenAI API interactions for the Disavowed game.
    It provides schema-aware prompt templates that ensure AI responses align
    with database field constraints and return structured JSON data.
    
    Key features:
    - Field length validation to prevent database errors
    - Structured JSON response parsing with safety checks
    - Template-based prompts for consistency
    - Error handling and logging for debugging
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4.1-nano-2025-04-14"  # Current model CHEAP!
        # self.model = "gpt-4-2025-04-14"  # Standard GPT-4 EXPENSIVE!
        # self.model = "o4-mini-2025-04-16"  # Reasoning version
        # self.model = "o3-2025-04-16"  # Ultra expensive reasoning version   VERY EXPENSIVE!
        
        # Database schema constraints for validation
        self.SCHEMA_LIMITS = {
            'mission_title': 200,
            'mission_description': 1000,  # Keep reasonable for UI
            'objective': 255,  # This maps to primary_conflict in DB
            'deadline': 200,
            'setting': 255,  # This was the main issue - needs to be 255, not 500
            'narrative_style': 100,
            'mood': 100,
            'opening_narrative': 1500,  # Reasonable for UI but not too long
            'choice_text': 255,  # Conservative for UI
            'primary_conflict': 255,  # Conservative for database compatibility
            'narrative_text': 1500,  # Reasonable length
            'character_name': 200,
            'next_node_summary': 255  # Conservative for UI
        }
    
    def safe_json_parse(self, raw_str):
        """
        Since OpenAI already returns valid JSON with response_format=json_object,
        just parse and validate against schema constraints.
        
        Args:
            raw_str (str): Raw JSON response string from OpenAI
            
        Returns:
            dict: Parsed and validated JSON object, or None if parsing fails
        """
        try:
            # OpenAI guarantees valid JSON with response_format=json_object
            parsed_response = json.loads(raw_str)
            
            # Validate and truncate fields according to schema limits
            validated_data = self._validate_and_truncate(parsed_response)
            
            logging.info(f"Successfully parsed and validated OpenAI JSON response")
            return validated_data
            
        except json.JSONDecodeError as e:
            logging.error(f"Unexpected JSON decode error (OpenAI should return valid JSON): {e}")
            logging.error(f"Raw response: {raw_str}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in safe_json_parse: {e}")
            return None
    
    def _validate_and_truncate(self, data):
        """
        Recursively validate and truncate string fields according to schema limits.
        Handles nested structures like choices arrays.
        
        Args:
            data: The data structure to validate (dict, list, or primitive)
            
        Returns:
            The validated and truncated data structure
        """
        if isinstance(data, dict):
            validated = {}
            for key, value in data.items():
                if isinstance(value, str) and key in self.SCHEMA_LIMITS:
                    max_length = self.SCHEMA_LIMITS[key]
                    if len(value) > max_length:
                        logging.warning(f"Truncating field '{key}' from {len(value)} to {max_length} characters")
                        validated[key] = value[:max_length]
                    else:
                        validated[key] = value
                elif isinstance(value, (dict, list)):
                    validated[key] = self._validate_and_truncate(value)
                else:
                    validated[key] = value
            return validated
        elif isinstance(data, list):
            return [self._validate_and_truncate(item) for item in data]
        else:
            return data
    
    def generate_full_mission_story(self, mission_giver, villain, partner, random_character, player_name, player_gender, narrative_style=None, mood=None):
        """
        Generate complete mission with story opening and 3 choices using schema-aware prompts.
        Returns structured JSON that aligns with database schema constraints.
        """
        try:
            pronouns = {'he/him': 'he', 'she/her': 'she', 'they/them': 'they'}.get(player_gender, 'they')
            
            # Set defaults if not provided
            if not narrative_style:
                narrative_style = 'Modern Espionage Thriller'
            if not mood:
                mood = 'Action-packed and Suspenseful'
            
            # Extract character info properly
            def get_character_info(char):
                # Use description if available, otherwise note they have an image
                if char.image_url:
                    desc = f"[See character image at {char.image_url}]"
                else:
                    desc = "Character appearance not described"
                
                # Extract traits
                traits = ""
                if char.character_traits:
                    if isinstance(char.character_traits, dict):
                        # Handle dict format like {'cunning': '', 'strategic': ''}
                        trait_list = []
                        for k, v in char.character_traits.items():
                            if v and v.strip():
                                trait_list.append(f"{k}: {v}")
                            else:
                                trait_list.append(k)
                        traits = ", ".join(trait_list)
                    elif isinstance(char.character_traits, list):
                        traits = ", ".join(char.character_traits)
                    else:
                        traits = str(char.character_traits)
                
                # Extract backstory
                backstory = ""
                if char.backstory:
                    if isinstance(char.backstory, str):
                        backstory = char.backstory
                    else:
                        backstory = str(char.backstory)
                
                result = desc
                if traits:
                    result += f" TRAITS: {traits}."
                if backstory:
                    result += f" BACKSTORY: {backstory}"
                
                return result
            
            giver_info = get_character_info(mission_giver)
            villain_info = get_character_info(villain)
            partner_info = get_character_info(partner)
            random_info = get_character_info(random_character)
            
            # Schema-aware prompt template with strict field length constraints
            prompt = f"""
You are creating a mission for an espionage thriller game. You MUST return ONLY a valid JSON object with the exact structure shown below. 

CRITICAL CONSTRAINTS:
- mission_title: Maximum 200 characters
- objective: No length limit (text field)
- deadline: Maximum 200 characters  
- setting: Maximum 255 characters
- narrative_style: Maximum 100 characters
- mood: Maximum 100 characters
- opening_narrative: No length limit but keep under 2000 characters for readability
- choice_text: No length limit but keep each choice under 255 characters for UI
- difficulty: Must be exactly one of: "low", "medium", "high"
- risk_level: Must be exactly one of: "low", "medium", "high"

JSON FORMATTING RULES:
- Do NOT include literal line breaks inside string values
- Use \\n for line breaks within strings if needed
- Ensure all strings are properly escaped
- Return valid, parseable JSON only

CHARACTERS:
- Player: {player_name} (pronouns: {pronouns})
- Mission Giver: {mission_giver.character_name} - {giver_info}
- Target/Villain: {villain.character_name} - {villain_info}  
- Partner: {partner.character_name} - {partner_info}
- Additional Character: {random_character.character_name} - {random_info}

REQUIREMENTS:
1. Create a mission where {mission_giver.character_name} briefs {player_name} to target {villain.character_name}
2. {partner.character_name} is assigned as the partner for this mission
3. Write an opening narrative in {narrative_style} style with {mood} mood that establishes the mission scenario using the character backgrounds
4. Generate exactly 3 distinct choices, each incorporating one of these characters: {partner.character_name}, {random_character.character_name}, or another creative option
5. Each choice should represent different risk levels and approaches (cautious, moderate, aggressive)
6. Make it action-packed espionage with stakes and tension, maintaining the {mood} mood

RESPONSE FORMAT (JSON) - NO LINE BREAKS IN STRING VALUES:
{{
  "mission_title": "Brief mission title (<=200 chars)",
  "mission_description": "2-3 paragraph mission briefing",
  "objective": "Clear, actionable mission goal",
  "difficulty": "medium",
  "deadline": "Time constraint description (<=200 chars)",
  "setting": "Concise location description (<=255 chars)",
  "narrative_style": "{narrative_style}",
  "mood": "{mood}",
  "opening_narrative": "2-3 paragraphs setting the scene and immediate situation",
  "choices": [
    {{
      "text": "First choice option",
      "character_used": "{partner.character_name}",
      "risk_level": "low",
      "next_node_summary": "Brief description of what happens if this choice is selected"
    }},
    {{
      "text": "Second choice option", 
      "character_used": "{random_character.character_name}",
      "risk_level": "medium",
      "next_node_summary": "Brief description of what happens if this choice is selected"
    }},
    {{
      "text": "Third choice option",
      "character_used": "{player_name}",
      "risk_level": "high", 
      "next_node_summary": "Brief description of what happens if this choice is selected"
    }}
  ]
}}

Create an engaging espionage mission that involves the mission giver assigning a task related to the villain. The player must work with their partner and the additional character. Make it exciting but ensure all text fits within the specified length limits.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional game narrative designer. You MUST return only valid JSON with no additional text or formatting. Do not include literal line breaks inside string values - use \\n for line breaks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            logging.info(f"Raw OpenAI response: {raw_response}")
            
            # Use safe parsing with schema validation
            parsed_response = self.safe_json_parse(raw_response)
            
            if not parsed_response:
                logging.error("Failed to parse OpenAI response as valid JSON")
                return None
                
            return parsed_response
            
        except Exception as e:
            logging.error(f"Error in generate_full_mission_story: {e}")
            return None
    
    def generate_mission(self, mission_giver):
        """
        Generate a mission briefing from a character using schema-aware prompts.
        Returns structured JSON that aligns with database schema constraints.
        """
        try:
            character_info = f"""
            Name: {mission_giver.character_name}
            Role: {mission_giver.character_role}
            Traits: {mission_giver.character_traits}
            Backstory: {mission_giver.backstory}
            """
            
            prompt = f"""You are creating a mission briefing for an irreverent espionage CYOA game. 
            The mission giver is: {character_info}
            
            Generate a mission that fits this character's devil-may-care personality and role. The game has a bold, 
            risk-taking attitude with high stakes espionage themes.
            
            Respond with JSON in this exact format:
            {{
                "title": "Mission title (<=200 chars)",
                "description": "Brief mission description (2-3 sentences)",
                "objective": "Clear objective statement",
                "difficulty": "easy/medium/hard",
                "deadline": "Narrative deadline description (<=200 chars)"
            }}
            
            Make it exciting but ensure all text fits within the specified length limits.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional game narrative designer. You MUST return only valid JSON with no additional text or formatting. Do not include literal line breaks inside string values - use \\n for line breaks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            logging.info(f"Raw OpenAI response: {raw_response}")
            
            # Use safe parsing with schema validation
            parsed_response = self.safe_json_parse(raw_response)
            
            if not parsed_response:
                logging.error("Failed to parse OpenAI response as valid JSON")
                return None
                
            return parsed_response
            
        except Exception as e:
            logging.error(f"Error in generate_mission: {e}")
            return None
    
    def generate_story_opening(self, mission, mission_giver):
        """
        Generate the opening narrative for a mission using schema-aware prompts.
        Returns structured JSON that aligns with database schema constraints.
        """
        try:
            character_name = mission_giver.character_name if mission_giver else "ERROR"
            
            prompt = f"""You are writing the opening scene for an irreverent espionage CYOA game.
            
            Mission: {mission.title}
            Description: {mission.description}
            Mission Giver: {character_name}
            
            Write a 2-3 paragraph opening that:
            1. Sets the scene with tension and espionage atmosphere
            2. Has the mission giver brief the player (a disavowed spy)
            3. Maintains a bold, risk-taking tone with high stakes
            4. Ends with the player about to make their first decision
            
            Respond with JSON in this exact format:
            {{
                "opening_narrative": "2-3 paragraphs setting the scene and immediate situation"
            }}
            
            Make it engaging but ensure all text fits within the specified length limits.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional game narrative designer. You MUST return only valid JSON with no additional text or formatting. Do not include literal line breaks inside string values - use \\n for line breaks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            logging.info(f"Raw OpenAI response: {raw_response}")
            
            # Use safe parsing with schema validation
            parsed_response = self.safe_json_parse(raw_response)
            
            if not parsed_response:
                logging.error("Failed to parse OpenAI response as valid JSON")
                return None
                
            return parsed_response
            
        except Exception as e:
            logging.error(f"Error in generate_story_opening: {e}")
            return None
    
    def generate_choices(self, current_narrative, character, game_state, available_characters=None):
        """
        Generate 3 AI choices for the current narrative, each incorporating a random character using schema-aware prompts.
        Returns structured JSON that aligns with database schema constraints.
        """
        try:
            character_info = ""
            if character:
                character_info = f"Current character: {character.character_name} ({character.character_role})"
            
            # Include available characters for incorporation into choices
            character_pool = ""
            if available_characters:
                character_pool = f"""
Available characters to incorporate into choices:
{chr(10).join([f"- {char.character_name}: {char.description[:100]}..." for char in available_characters[:6]])}
"""
            
            prompt = f"""You are generating choices for an irreverent espionage CYOA game.
            
            Current narrative: {current_narrative}
            {character_info}
            Game context: {json.dumps(game_state) if game_state else 'Starting mission'}
            {character_pool}
            
            Generate exactly 3 distinct choices that:
            1. Fit the espionage theme with bold, risky options
            2. Have different risk/reward levels (cautious, moderate, aggressive)
            3. Each choice should incorporate one of the available characters as an ally/contact/helper
            4. Each choice should be 1-2 sentences, actionable and specific
            5. Include potential consequences for each choice
            
            Respond with JSON in this exact format:
            {{
                "choices": [
                    {{
                        "text": "Choice 1 text mentioning character name",
                        "consequence": "Brief description of likely outcome",
                        "character_used": "Character Name",
                        "risk_level": "low/medium/high"
                    }},
                    {{
                        "text": "Choice 2 text mentioning character name",
                        "consequence": "Brief description of likely outcome",
                        "character_used": "Character Name",
                        "risk_level": "low/medium/high"
                    }},
                    {{
                        "text": "Choice 3 text mentioning character name",
                        "consequence": "Brief description of likely outcome",
                        "character_used": "Character Name",
                        "risk_level": "low/medium/high"
                    }}
                ]
            }}
            
            Make it engaging but ensure all text fits within the specified length limits.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional game narrative designer. You MUST return only valid JSON with no additional text or formatting. Do not include literal line breaks inside string values - use \\n for line breaks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            logging.info(f"Raw OpenAI response: {raw_response}")
            
            # Use safe parsing with schema validation
            parsed_response = self.safe_json_parse(raw_response)
            
            if not parsed_response:
                logging.error("Failed to parse OpenAI response as valid JSON")
                return None
                
            return parsed_response
            
        except Exception as e:
            logging.error(f"Error in generate_choices: {e}")
            return None
    
    def generate_story_continuation(self, previous_text, chosen_action, character, game_state):
        """
        Generate story continuation based on player choice using schema-aware prompts.
        Returns structured JSON that aligns with database schema constraints.
        """
        try:
            character_info = ""
            if character:
                character_info = f"Current character: {character.character_name}"
            
            prompt = f"""Continue this espionage story based on the player's choice. Use the game state to maintain context.
            
            Previous narrative: {previous_text} 
            Player's action: {chosen_action}
            {character_info}
            
            Write a meaningful continuation that:
            1. Shows the immediate consequences of the player's action
            2. Advances the story with new complications or revelations 
            3. Maintains context with the mission
            4. Sets up the next decision point
            5. Keeps the bold, risk-taking tone
            
            Respond with JSON in this exact format:
            {{
                "narrative_text": "Continuation of the story"
            }}
            
            Make it engaging but ensure all text fits within the specified length limits.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional game narrative designer. You MUST return only valid JSON with no additional text or formatting. Do not include literal line breaks inside string values - use \\n for line breaks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            logging.info(f"Raw OpenAI response: {raw_response}")
            
            # Use safe parsing with schema validation
            parsed_response = self.safe_json_parse(raw_response)
            
            if not parsed_response:
                logging.error("Failed to parse OpenAI response as valid JSON")
                return None
                
            return parsed_response
            
        except Exception as e:
            logging.error(f"Error in generate_story_continuation: {e}")
            return None
    
    def generate_custom_choice_response(self, current_text, custom_action, character, game_state):
        """
        Generate response to a custom user-input choice using schema-aware prompts.
        Returns structured JSON that aligns with database schema constraints.
        """
        try:
            character_info = ""
            if character:
                character_info = f"Current character: {character.character_name}"
            
            prompt = f"""Respond to a custom player action in this espionage story.
            
            Current situation: {current_text}
            Player's custom action: {custom_action}
            {character_info}
            
            Write a response that:
            1. Acknowledges and incorporates the player's creative action
            2. Shows realistic consequences (positive, negative, or mixed)
            3. Maintains story coherence and espionage theme
            4. Advances the plot in an interesting direction
            5. Keeps the bold, irreverent tone
            
            Respond with JSON in this exact format:
            {{
                "narrative_text": "Response to the custom choice"
            }}
            
            Make it impactful but ensure all text fits within the specified length limits.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional game narrative designer. You MUST return only valid JSON with no additional text or formatting. Do not include literal line breaks inside string values - use \\n for line breaks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            logging.info(f"Raw OpenAI response: {raw_response}")
            
            # Use safe parsing with schema validation
            parsed_response = self.safe_json_parse(raw_response)
            
            if not parsed_response:
                logging.error("Failed to parse OpenAI response as valid JSON")
                return None
                
            return parsed_response
            
        except Exception as e:
            logging.error(f"Error in generate_custom_choice_response: {e}")
            return None
