import logging
import random
from datetime import datetime
from app import db
from models import (UserProgress, Mission, Character, StoryNode, StoryChoice, 
                   Transaction, StoryGeneration, SceneImages)
from openai_integration import OpenAIIntegration

class GameEngine:
    """
    Core game logic engine for the espionage CYOA game
    Author: Cascade
    
    This engine orchestrates the game flow between the database, AI generation,
    and user interactions. It ensures data integrity and provides a seamless
    narrative experience by coordinating between story generation, mission
    management, and user progress tracking.
    
    Key features:
    - Schema-aware mission and story creation
    - Safe handling of AI-generated content with validation
    - Currency and progression management
    - Error handling and fallback mechanisms
    """
    
    def __init__(self):
        self.openai_integration = OpenAIIntegration()
        
        # Currency cost tiers for different choice types
        self.currency_tiers = {
            'low': {'💵': 5, '💷': 4, '💶': 4, '💴': 50},
            'medium': {'💵': 15, '💷': 12, '💶': 13, '💴': 150},
            'high': {'💵': 25, '💷': 20, '💶': 22, '💴': 250},
            'diamond': {'💎': 1}  # Premium choice
        }
    
    def create_full_mission(self, user_id, mission_giver, villain, partner, random_character, player_name, player_gender, narrative_style=None, mood=None):
        """
        Create complete mission with story opening and choices using schema-aware AI generation.
        Returns the created mission and initial story node, or None if creation fails.
        """
        try:
            # Set defaults if not provided
            if not narrative_style:
                narrative_style = 'Modern Espionage Thriller'
            if not mood:
                mood = 'Action-packed and Suspenseful'
            
            # Generate mission and story using OpenAI with all character context
            mission_story_data = self.openai_integration.generate_full_mission_story(
                mission_giver, villain, partner, random_character, player_name, player_gender, narrative_style, mood
            )
            
            if not mission_story_data:
                logging.error("Failed to generate mission story data from OpenAI")
                return None
            
            # Validate required fields are present
            required_fields = ['mission_title', 'mission_description', 'objective', 'opening_narrative', 'choices']
            for field in required_fields:
                if field not in mission_story_data:
                    logging.error(f"Missing required field '{field}' in OpenAI response")
                    return None
            
            # Create story generation record first
            story = StoryGeneration()
            story.primary_conflict = mission_story_data.get('objective', 'Complete mission objectives')
            story.setting = mission_story_data.get('setting', 'Various espionage locations')
            story.narrative_style = narrative_style  # Use user-provided value
            story.mood = mood  # Use user-provided value
            story.generated_story = {
                'characters': {
                    'mission_giver': mission_giver.id,
                    'villain': villain.id,
                    'partner': partner.id,
                    'random': random_character.id
                },
                'player': {'name': player_name, 'gender': player_gender},
                'ai_response': mission_story_data  # Store original AI response for debugging
            }
            db.session.add(story)
            db.session.flush()
            
            # Create mission record with story_id link
            mission = Mission()
            mission.user_id = user_id
            mission.title = mission_story_data.get('mission_title', 'Classified Operation')
            mission.description = mission_story_data.get('mission_description', 'Espionage mission')
            mission.giver_id = mission_giver.id
            mission.target_id = villain.id
            mission.objective = mission_story_data.get('objective', 'Complete mission objectives')
            mission.difficulty = mission_story_data.get('difficulty', 'medium')
            mission.reward_currency = '💎'
            mission.reward_amount = random.randint(2, 5)
            mission.deadline = mission_story_data.get('deadline', '48 hours')
            mission.story_id = story.id  # Critical link
            
            db.session.add(mission)
            db.session.flush()
            
            # Create initial story node with narrative
            story_node = StoryNode()
            story_node.story_id = story.id
            story_node.narrative_text = mission_story_data.get('opening_narrative', 'Mission begins...')
            story_node.character_id = mission_giver.id
            story_node.is_endpoint = False
            story_node.branch_metadata = {
                'mission_id': mission.id,
                'node_type': 'opening',
                'characters_present': [mission_giver.id, partner.id],
                'ai_generation_meta': {
                    'narrative_style': narrative_style,
                    'mood': mood,
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
            db.session.add(story_node)
            db.session.flush()
            
            # Create the 3 choices with currency costs and risk levels
            choices_data = mission_story_data.get('choices', [])
            if not choices_data:
                logging.error("No choices data provided in OpenAI response")
                return None
                
            cost_tiers = ['low', 'medium', 'high']
            
            for i, choice_data in enumerate(choices_data[:3]):
                if not isinstance(choice_data, dict):
                    logging.warning(f"Invalid choice data format at index {i}, skipping")
                    continue
                    
                # Map AI risk level to currency tier
                ai_risk_level = choice_data.get('risk_level', 'medium')
                if ai_risk_level in cost_tiers:
                    tier = ai_risk_level
                else:
                    tier = cost_tiers[i] if i < len(cost_tiers) else 'medium'
                
                currency_symbol = random.choice(list(self.currency_tiers[tier].keys()))
                currency_cost = self.currency_tiers[tier][currency_symbol]
                
                choice = StoryChoice()
                choice.node_id = story_node.id
                choice.choice_text = choice_data.get('text', 'Take action')
                choice.currency_requirements = {currency_symbol: currency_cost}
                choice.choice_metadata = {
                    'character_used': choice_data.get('character_used', 'Unknown'),
                    'risk_level': choice_data.get('risk_level', 'medium'),
                    'next_node_summary': choice_data.get('next_node_summary', ''),
                    'tier': tier,
                    'ai_generated': True
                }
                
                db.session.add(choice)
            
            # Commit all changes
            db.session.commit()
            
            logging.info(f"Successfully created mission '{mission.title}' for user {user_id}")
            return mission, story_node
            
        except Exception as e:
            logging.error(f"Error creating full mission: {e}")
            db.session.rollback()
            return None
    
    def start_mission_story(self, user_id, mission_id):
        """
        Start the story for a mission
        """
        try:
            mission = Mission.query.get(mission_id)
            if not mission or mission.user_id != user_id:
                return None
            
            # Create initial story generation
            story = StoryGeneration()
            story.primary_conflict = mission.objective
            story.setting = "Various espionage locations"
            story.narrative_style = "Action-packed thriller"
            story.mood = "Tense and suspenseful"
            story.generated_story = {"mission_id": mission_id}
            db.session.add(story)
            db.session.flush()  # Get the ID
            
            # Generate initial story node
            opening_data = self.openai_integration.generate_story_opening(mission, mission.giver)
            
            if not opening_data:
                logging.error("Failed to generate story opening from OpenAI")
                return None
            
            # Extract opening narrative from structured JSON response
            initial_text = opening_data.get('opening_narrative', 'The mission begins with high stakes and danger lurking around every corner...')
            
            story_node = StoryNode()
            story_node.story_id = story.id
            story_node.narrative_text = initial_text
            story_node.character_id = mission.giver_id
            story_node.is_endpoint = False
            story_node.branch_metadata = {"mission_id": mission_id, "node_type": "opening"}
            db.session.add(story_node)
            db.session.flush()  # Get the ID
            
            # Update user progress
            user_progress = UserProgress.query.filter_by(user_id=user_id).first()
            user_progress.current_node_id = story_node.id
            user_progress.current_story_id = story.id
            
            db.session.commit()
            return story_node
            
        except Exception as e:
            logging.error(f"Error starting mission story: {e}")
            db.session.rollback()
            return None
    
    def generate_choices_for_node(self, node, user_progress):
        """
        Generate 4 choices for a story node (3 AI + 1 custom)
        """
        try:
            # Get random characters from database for choices
            from models import Character
            available_characters = Character.query.order_by(db.func.random()).limit(6).all()
            
            # Generate 3 AI choices with different cost tiers
            choices_response = self.openai_integration.generate_choices(
                node.narrative_text, 
                node.character, 
                user_progress.game_state,
                available_characters
            )
            
            if not choices_response:
                logging.error("Failed to generate choices from OpenAI")
                return []
            
            # Extract choices array from structured JSON response
            ai_choices_data = choices_response.get('choices', [])
            
            choices = []
            cost_tiers = ['low', 'medium', 'high']
            
            for i, choice_data in enumerate(ai_choices_data[:3]):
                if not isinstance(choice_data, dict):
                    logging.warning(f"Invalid choice data format at index {i}, skipping")
                    continue
                    
                # Assign currency cost based on tier or risk level
                ai_risk_level = choice_data.get('risk_level', 'medium')
                if ai_risk_level in cost_tiers:
                    tier = ai_risk_level
                else:
                    tier = cost_tiers[i] if i < len(cost_tiers) else 'medium'
                    
                currency_symbol = random.choice(list(self.currency_tiers[tier].keys()))
                currency_cost = self.currency_tiers[tier][currency_symbol]
                
                choice = StoryChoice()
                choice.node_id = node.id
                choice.choice_text = choice_data.get('text', 'Take action')
                choice.currency_requirements = {currency_symbol: currency_cost}
                choice.choice_metadata = {
                    'tier': tier,
                    'ai_generated': True,
                    'consequence': choice_data.get('consequence', ''),
                    'character_used': choice_data.get('character_used', 'Unknown'),
                    'risk_level': choice_data.get('risk_level', 'medium')
                }
                db.session.add(choice)
                choices.append(choice)
            
            db.session.commit()
            return choices
            
        except Exception as e:
            logging.error(f"Error generating choices: {e}")
            db.session.rollback()
            return []
    
    def can_afford_choice(self, user_progress, choice):
        """
        Check if user can afford a choice
        """
        if not choice.currency_requirements:
            return True
        
        user_balances = user_progress.currency_balances or {}
        
        for currency, amount in choice.currency_requirements.items():
            user_amount = user_balances.get(currency, 0)
            if user_amount < amount:
                return False
        
        return True
    
    def process_choice(self, user_progress, choice):
        """
        Process a user's choice selection
        """
        try:
            # Check if user can afford the choice
            if not self.can_afford_choice(user_progress, choice):
                return {
                    'success': False,
                    'message': 'Insufficient currency for this choice'
                }
            
            # Deduct currency
            self._deduct_currency(user_progress, choice.currency_requirements)
            
            # Record transaction
            for currency, amount in choice.currency_requirements.items():
                transaction = Transaction(
                    user_id=user_progress.user_id,
                    transaction_type='choice',
                    from_currency=currency,
                    amount=amount,
                    description=f"Choice: {choice.choice_text[:50]}...",
                    story_node_id=choice.node_id
                )
                db.session.add(transaction)
            
            # Generate next story node
            next_node = self._generate_next_node(choice, user_progress)
            
            if next_node:
                user_progress.current_node_id = next_node.id
                
                # Update choice history
                choice_history = user_progress.choice_history or []
                choice_history.append({
                    'choice_id': choice.id,
                    'choice_text': choice.choice_text,
                    'timestamp': datetime.utcnow().isoformat(),
                    'node_id': choice.node_id
                })
                user_progress.choice_history = choice_history
                
                db.session.commit()
                return {'success': True, 'next_node': next_node}
            else:
                return {
                    'success': False,
                    'message': 'Failed to generate next story segment'
                }
                
        except Exception as e:
            logging.error(f"Error processing choice: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': 'Server error processing choice'
            }
    
    def process_custom_choice(self, user_progress, custom_text):
        """
        Process a custom user-input choice (costs diamonds)
        """
        try:
            # Check diamond balance
            diamond_cost = self.currency_tiers['diamond']['💎']
            user_balances = user_progress.currency_balances or {}
            
            if user_balances.get('💎', 0) < diamond_cost:
                return {
                    'success': False,
                    'message': 'Insufficient diamonds for custom choice'
                }
            
            # Deduct diamonds
            self._deduct_currency(user_progress, {'💎': diamond_cost})
            
            # Record transaction
            transaction = Transaction(
                user_id=user_progress.user_id,
                transaction_type='custom_choice',
                from_currency='💎',
                amount=diamond_cost,
                description=f"Custom choice: {custom_text[:50]}...",
                story_node_id=user_progress.current_node_id
            )
            db.session.add(transaction)
            
            # Generate response to custom choice
            current_node = StoryNode.query.get(user_progress.current_node_id)
            next_node = self._generate_custom_response_node(current_node, custom_text, user_progress)
            
            if next_node:
                user_progress.current_node_id = next_node.id
                
                # Update choice history
                choice_history = user_progress.choice_history or []
                choice_history.append({
                    'choice_text': custom_text,
                    'timestamp': datetime.utcnow().isoformat(),
                    'node_id': current_node.id,
                    'custom': True
                })
                user_progress.choice_history = choice_history
                
                db.session.commit()
                return {'success': True, 'next_node': next_node}
            else:
                return {
                    'success': False,
                    'message': 'Failed to process custom choice'
                }
                
        except Exception as e:
            logging.error(f"Error processing custom choice: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': 'Server error processing custom choice'
            }
    
    def _deduct_currency(self, user_progress, currency_requirements):
        """
        Deduct currency from user balance
        """
        balances = user_progress.currency_balances or {}
        
        for currency, amount in currency_requirements.items():
            current_balance = balances.get(currency, 0)
            balances[currency] = max(0, current_balance - amount)
        
        user_progress.currency_balances = balances
    
    def _generate_next_node(self, choice, user_progress):
        """
        Generate the next story node based on choice
        """
        try:
            # If choice already has a next_node_id, use it
            if choice.next_node_id:
                return StoryNode.query.get(choice.next_node_id)
            
            # Generate new node using AI
            current_node = StoryNode.query.get(choice.node_id)
            response_data = self.openai_integration.generate_story_continuation(
                current_node.narrative_text,
                choice.choice_text,
                current_node.character,
                user_progress.game_state
            )
            
            if not response_data:
                logging.error("Failed to generate story continuation from OpenAI")
                return None
            
            # Extract narrative text from structured JSON response
            narrative_text = response_data.get('narrative_text', 'Your bold action creates unexpected consequences...')
            
            next_node = StoryNode(
                story_id=current_node.story_id,
                narrative_text=narrative_text,
                character_id=current_node.character_id,
                parent_node_id=current_node.id,
                branch_metadata=current_node.branch_metadata
            )
            
            db.session.add(next_node)
            db.session.flush()
            
            # Update the choice to point to this node
            choice.next_node_id = next_node.id
            
            return next_node
            
        except Exception as e:
            logging.error(f"Error generating next node: {e}")
            return None
    
    def _generate_custom_response_node(self, current_node, custom_choice, user_progress):
        """
        Generate response to custom user choice
        """
        try:
            response_data = self.openai_integration.generate_custom_choice_response(
                current_node.narrative_text,
                custom_choice,
                current_node.character,
                user_progress.game_state
            )
            
            if not response_data:
                logging.error("Failed to generate custom choice response from OpenAI")
                return None
            
            # Extract narrative text from structured JSON response
            narrative_text = response_data.get('narrative_text', 'Your bold action creates unexpected consequences...')
            
            next_node = StoryNode(
                story_id=current_node.story_id,
                narrative_text=narrative_text,
                character_id=current_node.character_id,
                parent_node_id=current_node.id,
                branch_metadata=current_node.branch_metadata
            )
            
            db.session.add(next_node)
            db.session.flush()
            
            return next_node
            
        except Exception as e:
            logging.error(f"Error generating custom response node: {e}")
            return None
