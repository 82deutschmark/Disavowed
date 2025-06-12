import json
import os
import logging
from openai import OpenAI

class OpenAIIntegration:
    """Integration with OpenAI for dynamic story generation"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4.1-nano-2025-04-14"  # Current model CHEAP!
        # self.model = "gpt-4.1-2025-04-14"  # Standard GPT-4 EXPENSIVE!
        # self.model = "o4-mini-2025-04-16"  # Reasoning version
        # self.model = "o3-2025-04-16"  # Ultra expensive reasoning version   VERY EXPENSIVE!
    
    def generate_full_mission_story(self, mission_giver, villain, partner, random_character, player_name, player_gender):
        """Generate complete mission with story opening and 3 choices"""
        try:
            import json as json_lib
            pronouns = {'he/him': 'he', 'she/her': 'she', 'they/them': 'they'}.get(player_gender, 'they')
            
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
            
            mission_giver_info = get_character_info(mission_giver)
            villain_info = get_character_info(villain)  
            partner_info = get_character_info(partner)
            random_info = get_character_info(random_character)
            
            prompt = f"""You are creating an espionage CYOA game scenario. Generate a complete mission briefing and opening story segment with exactly 3 choices.

CHARACTERS:
- Player: {player_name} (pronouns: {pronouns})
- Mission Giver: {mission_giver.character_name} - {mission_giver_info}
- Target/Villain: {villain.character_name} - {villain_info}  
- Partner: {partner.character_name} - {partner_info}
- Additional Character: {random_character.character_name} - {random_info}

REQUIREMENTS:
1. Create a mission where {mission_giver.character_name} briefs {player_name} to target {villain.character_name}
2. {partner.character_name} is assigned as the partner for this mission
3. Write an opening narrative that establishes the mission scenario using the character backgrounds
4. Generate exactly 3 distinct choices, each incorporating one of these characters: {partner.character_name}, {random_character.character_name}, or another creative option
5. Each choice should represent different risk levels and approaches (cautious, moderate, aggressive)
6. Make it action-packed espionage with stakes and tension

RESPONSE FORMAT (JSON):
{{
    "mission_title": "Compelling mission title",
    "mission_description": "Brief mission summary", 
    "objective": "Clear mission objective",
    "difficulty": "medium",
    "deadline": "48 hours",
    "setting": "Location/environment description",
    "opening_narrative": "2-3 paragraph story opening that introduces the mission briefing and sets up the choices",
    "choices": [
        {{
            "text": "Choice 1 - mention {partner.character_name} specifically in this action",
            "character_used": "{partner.character_name}",
            "risk_level": "low"
        }},
        {{
            "text": "Choice 2 - mention {random_character.character_name} specifically in this action", 
            "character_used": "{random_character.character_name}",
            "risk_level": "medium"
        }},
        {{
            "text": "Choice 3 - aggressive solo action or creative approach",
            "character_used": "solo",
            "risk_level": "high"
        }}
    ]
}}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logging.error(f"Error generating full mission story: {e}")
            return None

    def generate_mission(self, mission_giver):
        """Generate a mission briefing from a character"""
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
                "title": "Mission title",
                "description": "Brief mission description (2-3 sentences)",
                "objective": "Clear objective statement",
                "difficulty": "easy/medium/hard",
                "deadline": "Narrative deadline description"
            }}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content or "{}")
            
        except Exception as e:
            logging.error(f"Error generating mission: {e}")
            return {
                "title": "Classified Operation",
                "description": "A dangerous mission awaits. Your contact needs someone expendable.",
                "objective": "Complete the mission objectives without getting killed.",
                "difficulty": "medium",
                "deadline": "24 hours"
            }
    
    def generate_story_opening(self, mission, mission_giver):
        """Generate the opening narrative for a mission"""
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
            
            Keep it engaging and immersive, around 150-200 words."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error generating story opening: {e}")
            handler_name = mission_giver.character_name if mission_giver else "Your Handler"
            return f"Your handler {handler_name} slides a dossier across the table. The mission is simple but dangerous: {mission.description}. Time is running out, and you're the only agent available. What's your first move?"
    
    def generate_choices(self, current_narrative, character, game_state, available_characters=None):
        """Generate 3 AI choices for the current narrative, each incorporating a random character"""
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
                    {{"text": "Choice 1 text mentioning character name", "consequence": "Brief description of likely outcome", "character_used": "Character Name"}},
                    {{"text": "Choice 2 text mentioning character name", "consequence": "Brief description of likely outcome", "character_used": "Character Name"}},
                    {{"text": "Choice 3 text mentioning character name", "consequence": "Brief description of likely outcome", "character_used": "Character Name"}}
                ]
            }}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                return result.get("choices", [])
            return []
            
        except Exception as e:
            logging.error(f"Error generating choices: {e}")
            return [
                {"text": "Take the direct approach", "consequence": "High risk, high reward"},
                {"text": "Gather more intelligence first", "consequence": "Safer but time-consuming"},
                {"text": "Find an alternative route", "consequence": "Unpredictable outcome"}
            ]
    
    def generate_story_continuation(self, previous_text, chosen_action, character, game_state):
        """Generate story continuation based on player choice"""
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
            
            Around 1500-2000 words."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error generating story continuation: {e}")
            return f"You decide to {chosen_action.lower()}. The situation becomes more complex as new challenges emerge. Your next move will be crucial to the mission's success."
    
    def generate_custom_choice_response(self, current_text, custom_action, character, game_state):
        """Generate response to a custom user-input choice"""
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
            
            The player paid premium currency for this choice, so make it impactful.
            Around 1500-2000 words."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error generating custom choice response: {e}")
            return f"Your bold decision to {custom_action} catches everyone off guard. The unexpected move creates new opportunities, but also new dangers. The mission takes an interesting turn."
