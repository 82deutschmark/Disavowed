import logging
from flask import render_template, request, session, redirect, url_for, jsonify, flash
from app import app, db
from models import UserProgress, Character, Mission, StoryNode, StoryChoice, SceneImages, StoryGeneration
from game_engine import GameEngine
from openai_integration import OpenAIIntegration
import uuid

# Initialize game components
game_engine = GameEngine()
openai_integration = OpenAIIntegration()

@app.route('/')
def index():
    """Landing page for the espionage game"""
    try:
        # Get some sample characters for display
        sample_characters = Character.query.limit(6).all()
        return render_template('index.html', characters=sample_characters)
    except Exception as e:
        logging.error(f"Error loading index page: {e}")
        return render_template('index.html', characters=[], error="Failed to load character data")

@app.route('/start_game')
def start_game():
    """Initialize a new game session"""
    try:
        # Generate or get user ID
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        user_id = session['user_id']
        
        # Get or create user progress
        user_progress = UserProgress.query.filter_by(user_id=user_id).first()
        if not user_progress:
            user_progress = UserProgress(user_id=user_id)
            db.session.add(user_progress)
            db.session.commit()
        
        # If user has no current mission, assign one
        if not user_progress.active_missions:
            return redirect(url_for('mission_assignment'))
        else:
            return redirect(url_for('game'))
            
    except Exception as e:
        logging.error(f"Error starting game: {e}")
        flash("Failed to start game. Please try again.", "error")
        return redirect(url_for('index'))

@app.route('/mission_assignment')
def mission_assignment():
    """Assign a new mission to the player"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('start_game'))
        
        # Get a random mission giver character
        mission_giver = Character.query.filter_by(character_role='mission-giver').first()
        if not mission_giver:
            # Fallback to any character
            mission_giver = Character.query.first()
        
        if not mission_giver:
            flash("No characters available for mission assignment.", "error")
            return redirect(url_for('index'))
        
        # Create a new mission using the game engine
        mission = game_engine.create_mission(user_id, mission_giver)
        
        # Get user progress for currency display
        user_progress = UserProgress.query.filter_by(user_id=user_id).first()
        
        return render_template('mission_assignment.html', 
                             mission=mission, 
                             mission_giver=mission_giver,
                             user_progress=user_progress)
                             
    except Exception as e:
        logging.error(f"Error in mission assignment: {e}")
        flash("Failed to assign mission. Please try again.", "error")
        return redirect(url_for('index'))

@app.route('/accept_mission/<int:mission_id>')
def accept_mission(mission_id):
    """Accept a mission and start the story"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('start_game'))
        
        # Start the story for this mission
        story_node = game_engine.start_mission_story(user_id, mission_id)
        
        if story_node:
            return redirect(url_for('game'))
        else:
            flash("Failed to start mission story.", "error")
            return redirect(url_for('mission_assignment'))
            
    except Exception as e:
        logging.error(f"Error accepting mission: {e}")
        flash("Failed to accept mission. Please try again.", "error")
        return redirect(url_for('mission_assignment'))

@app.route('/game')
def game():
    """Main game interface"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('start_game'))
        
        user_progress = UserProgress.query.filter_by(user_id=user_id).first()
        if not user_progress or not user_progress.current_node_id:
            return redirect(url_for('mission_assignment'))
        
        current_node = StoryNode.query.get(user_progress.current_node_id)
        if not current_node:
            flash("Story node not found. Starting new mission.", "warning")
            return redirect(url_for('mission_assignment'))
        
        # Get scene image if available
        scene_image = None
        if current_node.story_id:
            scene_image = SceneImages.query.first()  # For now, use any scene image
        
        # Get character if associated
        character = current_node.character
        
        # Generate choices using AI if needed
        choices = StoryChoice.query.filter_by(node_id=current_node.id).all()
        
        if not choices:
            # Generate new choices using AI
            choices = game_engine.generate_choices_for_node(current_node, user_progress)
        
        return render_template('game.html',
                             current_node=current_node,
                             choices=choices,
                             user_progress=user_progress,
                             character=character,
                             scene_image=scene_image)
                             
    except Exception as e:
        logging.error(f"Error in game route: {e}")
        flash("Game error occurred. Please try again.", "error")
        return redirect(url_for('index'))

@app.route('/make_choice', methods=['POST'])
def make_choice():
    """Process a player's choice"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('start_game'))
        
        choice_id = request.form.get('choice_id')
        custom_choice = request.form.get('custom_choice', '').strip()
        
        user_progress = UserProgress.query.filter_by(user_id=user_id).first()
        
        if choice_id:
            # Process pre-generated choice
            choice = StoryChoice.query.get(choice_id)
            if choice:
                result = game_engine.process_choice(user_progress, choice)
                if result['success']:
                    return redirect(url_for('game'))
                else:
                    flash(result['message'], 'error')
                    return redirect(url_for('game'))
        elif custom_choice:
            # Process custom diamond choice
            result = game_engine.process_custom_choice(user_progress, custom_choice)
            if result['success']:
                return redirect(url_for('game'))
            else:
                flash(result['message'], 'error')
                return redirect(url_for('game'))
        
        flash("Invalid choice selection.", "error")
        return redirect(url_for('game'))
        
    except Exception as e:
        logging.error(f"Error processing choice: {e}")
        flash("Failed to process choice. Please try again.", "error")
        return redirect(url_for('game'))

@app.route('/api/currency_check')
def currency_check():
    """API endpoint to check if user has enough currency for a choice"""
    try:
        user_id = session.get('user_id')
        choice_id = request.args.get('choice_id')
        
        if not user_id or not choice_id:
            return jsonify({'success': False, 'message': 'Missing parameters'})
        
        user_progress = UserProgress.query.filter_by(user_id=user_id).first()
        choice = StoryChoice.query.get(choice_id)
        
        if not user_progress or not choice:
            return jsonify({'success': False, 'message': 'User or choice not found'})
        
        can_afford = game_engine.can_afford_choice(user_progress, choice)
        
        return jsonify({
            'success': True,
            'can_afford': can_afford,
            'currency_balances': user_progress.currency_balances
        })
        
    except Exception as e:
        logging.error(f"Error checking currency: {e}")
        return jsonify({'success': False, 'message': 'Server error'})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('index.html', error="Internal server error"), 500
