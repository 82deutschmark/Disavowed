import logging
import random
from datetime import datetime
from app import db
from models import (UserProgress, Mission, Character, StoryNode, StoryChoice, 
                   Transaction, StoryGeneration, SceneImages)
from openai_integration import OpenAIIntegration

class GameEngine:
    """Core game logic engine for the espionage CYOA game"""
    
    def __init__(self):
        self.openai_integration = OpenAIIntegration()
        
        # Currency cost tiers for different choice types
        self.currency_tiers = {
            'low': {'💵': 5, '💷': 4, '💶': 4, '💴': 50},
            'medium': {'💵': 15, '💷': 12, '💶': 13, '💴': 150},
            'high': {'💵': 25, '💷': 20, '💶': 22, '💴': 250},
            'diamond': {'💎': 1}  # Premium choice
        }
    
    def create_mission(self, user_id, mission_giver):
        """Create a new mission for the user"""
        try:
            # Generate mission details using AI
            mission_data = self.openai_integration.generate_mission(mission_giver)
            
            # Create mission record
            mission = Mission(
                user_id=user_id,
                title=mission_data.get('title', 'Classified Operation'),
                description=mission_data.get('description', 'A dangerous espionage mission'),
                giver_id=mission_giver.id,
                objective=mission_data.get('objective', 'Complete the mission objectives'),
                difficulty=mission_data.get('difficulty', 'medium'),
                reward_currency='💎',
                reward_amount=random.randint(2, 5),
                deadline=mission_data.get('deadline', '48 hours')
            )
            
            db.session.add(mission)
            db.session.commit()
            
            # Update user progress
            user_progress = UserProgress.query.filter_by(user_id=user_id).first()
            if user_progress:
                active_missions = user_progress.active_missions or []
                active_missions.append(mission.id)
                user_progress.active_missions = active_missions
                db.session.commit()
            
            return mission
            
        except Exception as e:
            logging.error(f"Error creating mission: {e}")
            db.session.rollback()
            return None
    
    def start_mission_story(self, user_id, mission_id):
        """Start the story for a mission"""
        try:
            mission = Mission.query.get(mission_id)
            if not mission or mission.user_id != user_id:
                return None
            
            # Create initial story generation
            story = StoryGeneration(
                primary_conflict=mission.objective,
                setting="Various espionage locations",
                narrative_style="Action-packed thriller",
                mood="Tense and suspenseful",
                generated_story={"mission_id": mission_id}
            )
            db.session.add(story)
            db.session.flush()  # Get the ID
            
            # Generate initial story node
            initial_text = self.openai_integration.generate_story_opening(mission, mission.giver)
            
            story_node = StoryNode(
                story_id=story.id,
                narrative_text=initial_text,
                character_id=mission.giver_id,
                is_endpoint=False,
                branch_metadata={"mission_id": mission_id, "node_type": "opening"}
            )
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
        """Generate 4 choices for a story node (3 AI + 1 custom)"""
        try:
            # Get random neutral/undefined characters from database for choices
            from models import Character
            available_characters = Character.query.filter(
                Character.character_role.in_(['neutral', 'undetermined'])
            ).order_by(db.func.random()).limit(6).all()
            
            # Generate 3 AI choices with different cost tiers
            ai_choices_data = self.openai_integration.generate_choices(
                node.narrative_text, 
                node.character, 
                user_progress.game_state,
                available_characters
            )
            
            choices = []
            cost_tiers = ['low', 'medium', 'high']
            
            for i, choice_data in enumerate(ai_choices_data[:3]):
                # Assign currency cost based on tier
                tier = cost_tiers[i] if i < len(cost_tiers) else 'medium'
                currency_symbol = random.choice(list(self.currency_tiers[tier].keys()))
                currency_cost = self.currency_tiers[tier][currency_symbol]
                
                choice = StoryChoice(
                    node_id=node.id,
                    choice_text=choice_data['text'],
                    currency_requirements={currency_symbol: currency_cost},
                    choice_metadata={
                        'tier': tier,
                        'ai_generated': True,
                        'consequence': choice_data.get('consequence', '')
                    }
                )
                db.session.add(choice)
                choices.append(choice)
            
            db.session.commit()
            return choices
            
        except Exception as e:
            logging.error(f"Error generating choices: {e}")
            db.session.rollback()
            return []
    
    def can_afford_choice(self, user_progress, choice):
        """Check if user can afford a choice"""
        if not choice.currency_requirements:
            return True
        
        user_balances = user_progress.currency_balances or {}
        
        for currency, amount in choice.currency_requirements.items():
            user_amount = user_balances.get(currency, 0)
            if user_amount < amount:
                return False
        
        return True
    
    def process_choice(self, user_progress, choice):
        """Process a user's choice selection"""
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
        """Process a custom user-input choice (costs diamonds)"""
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
        """Deduct currency from user balance"""
        balances = user_progress.currency_balances or {}
        
        for currency, amount in currency_requirements.items():
            current_balance = balances.get(currency, 0)
            balances[currency] = max(0, current_balance - amount)
        
        user_progress.currency_balances = balances
    
    def _generate_next_node(self, choice, user_progress):
        """Generate the next story node based on choice"""
        try:
            # If choice already has a next_node_id, use it
            if choice.next_node_id:
                return StoryNode.query.get(choice.next_node_id)
            
            # Generate new node using AI
            current_node = StoryNode.query.get(choice.node_id)
            narrative_text = self.openai_integration.generate_story_continuation(
                current_node.narrative_text,
                choice.choice_text,
                current_node.character,
                user_progress.game_state
            )
            
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
        """Generate response to custom user choice"""
        try:
            narrative_text = self.openai_integration.generate_custom_choice_response(
                current_node.narrative_text,
                custom_choice,
                current_node.character,
                user_progress.game_state
            )
            
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
