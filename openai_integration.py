import json
import os
import logging
from openai import OpenAI

class OpenAIIntegration:
    """Integration with OpenAI for dynamic story generation"""
    
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
    
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
            
            Generate a mission that fits this character's personality and role. The game has a bold, 
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
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logging.error(f"Error generating mission: {e}")
            return {
                "title": "Classified Operation",
                "description": "A dangerous mission awaits. Your agency needs someone expendable.",
                "objective": "Complete the mission objectives without getting killed.",
                "difficulty": "medium",
                "deadline": "24 hours"
            }
    
    def generate_story_opening(self, mission, mission_giver):
        """Generate the opening narrative for a mission"""
        try:
            character_name = mission_giver.character_name if mission_giver else "Your Handler"
            
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
            return f"Your handler {character_name} slides a dossier across the table. The mission is simple but dangerous: {mission.description}. Time is running out, and you're the only agent available. What's your first move?"
    
    def generate_choices(self, current_narrative, character, game_state):
        """Generate 3 AI choices for the current narrative"""
        try:
            character_info = ""
            if character:
                character_info = f"Current character: {character.character_name} ({character.character_role})"
            
            prompt = f"""You are generating choices for an irreverent espionage CYOA game.
            
            Current narrative: {current_narrative}
            {character_info}
            Game context: {json.dumps(game_state) if game_state else 'Starting mission'}
            
            Generate exactly 3 distinct choices that:
            1. Fit the espionage theme with bold, risky options
            2. Have different risk/reward levels (cautious, moderate, aggressive)
            3. Each choice should be 1-2 sentences, actionable and specific
            4. Include potential consequences for each choice
            
            Respond with JSON in this exact format:
            {{
                "choices": [
                    {{"text": "Choice 1 text", "consequence": "Brief description of likely outcome"}},
                    {{"text": "Choice 2 text", "consequence": "Brief description of likely outcome"}},
                    {{"text": "Choice 3 text", "consequence": "Brief description of likely outcome"}}
                ]
            }}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("choices", [])
            
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
            
            prompt = f"""Continue this espionage story based on the player's choice.
            
            Previous narrative: {previous_text}
            Player's action: {chosen_action}
            {character_info}
            
            Write a 2-3 paragraph continuation that:
            1. Shows the immediate consequences of the player's action
            2. Advances the story with new complications or revelations
            3. Maintains tension and espionage atmosphere
            4. Sets up the next decision point
            5. Keeps the bold, risk-taking tone
            
            Around 150-200 words."""
            
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
            Around 150-200 words."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error generating custom choice response: {e}")
            return f"Your bold decision to {custom_action} catches everyone off guard. The unexpected move creates new opportunities, but also new dangers. The mission takes an interesting turn."
