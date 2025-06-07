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

@app.route('/start_game', methods=['GET', 'POST'])
def start_game():
    """Player setup - name, gender, character selection"""
    try:
        if request.method == 'GET':
            # Show character selection directly with name input
            mission_givers = Character.query.filter_by(character_role='mission-giver').all()
            villains = Character.query.filter_by(character_role='villain').all()
            partners = Character.query.filter(Character.character_role.in_(['neutral', 'undetermined'])).all()
            
            # Pre-process character traits for display
            for char in mission_givers + villains + partners:
                if char.character_traits and isinstance(char.character_traits, list):
                    char.display_traits = ', '.join(char.character_traits[:3])
                else:
                    char.display_traits = ''
            
            return render_template('start_game.html',
                                 mission_givers=mission_givers,
                                 villains=villains,
                                 partners=partners)
        
        # Process complete form submission
        player_name = request.form.get('player_name')
        player_gender = request.form.get('player_gender', 'they/them')
        mission_giver_id = request.form.get('mission_giver_id')
        villain_id = request.form.get('villain_id')
        partner_id = request.form.get('partner_id')
        
        if not all([player_name, mission_giver_id, villain_id, partner_id]):
            flash("Please fill in all fields.", "error")
            return redirect(url_for('start_game'))
        
        if player_name:
            player_name = player_name.strip()
        
        # Generate or get user ID
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        user_id = session['user_id']
        session['player_name'] = player_name
        session['player_gender'] = player_gender
        
        # Get selected characters
        mission_giver = Character.query.get(mission_giver_id)
        villain = Character.query.get(villain_id)
        partner = Character.query.get(partner_id)
        
        # Pick random additional character for choices
        random_character = Character.query.order_by(db.func.random()).first()
        
        # Generate mission and first story segment with choices
        mission_data = game_engine.create_full_mission(
            user_id, mission_giver, villain, partner, random_character,
            player_name, player_gender
        )
        
        if mission_data:
            return redirect(url_for('game'))
        else:
            flash("Failed to generate mission. Please try again.", "error")
            return redirect(url_for('start_game'))
            
    except Exception as e:
        logging.error(f"Error starting game: {e}")
        flash("Failed to start game. Please try again.", "error")
        return redirect(url_for('index'))

@app.route('/character_selection', methods=['GET', 'POST'])
def character_selection():
    """Character selection flow: mission giver -> villain -> partner"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            logging.error("No user_id in session")
            return redirect(url_for('start_game'))
        
        if request.method == 'GET':
            # Show character selection interface
            mission_givers = Character.query.filter_by(character_role='mission-giver').all()
            villains = Character.query.filter_by(character_role='villain').all()
            partners = Character.query.filter(Character.character_role.in_(['neutral', 'undetermined'])).all()
            
            return render_template('character_selection.html',
                                 mission_givers=mission_givers,
                                 villains=villains,
                                 partners=partners)
        
        # Process character selections
        mission_giver_id = request.form.get('mission_giver_id')
        villain_id = request.form.get('villain_id')
        partner_id = request.form.get('partner_id')
        
        if not all([mission_giver_id, villain_id, partner_id]):
            flash("Please select all required characters.", "error")
            return redirect(url_for('character_selection'))
        
        # Store selections in session
        session['mission_giver_id'] = mission_giver_id
        session['villain_id'] = villain_id
        session['partner_id'] = partner_id
        
        return redirect(url_for('generate_mission'))
                             
    except Exception as e:
        logging.error(f"Error in character selection: {e}")
        flash("Failed to process character selection.", "error")
        return redirect(url_for('start_game'))

@app.route('/generate_mission')
def generate_mission():
    """Generate mission using OpenAI with selected characters"""
    try:
        user_id = session.get('user_id')
        mission_giver_id = session.get('mission_giver_id')
        villain_id = session.get('villain_id')
        partner_id = session.get('partner_id')
        player_name = session.get('player_name')
        player_gender = session.get('player_gender')
        
        if not all([user_id, mission_giver_id, villain_id, partner_id]):
            return redirect(url_for('character_selection'))
        
        # Get selected characters
        mission_giver = Character.query.get(mission_giver_id)
        villain = Character.query.get(villain_id)
        partner = Character.query.get(partner_id)
        
        # Pick random additional character for choices
        random_character = Character.query.order_by(db.func.random()).first()
        
        # Generate mission and first story segment with choices
        mission_data = game_engine.create_full_mission(
            user_id, mission_giver, villain, partner, random_character,
            player_name, player_gender
        )
        
        if mission_data:
            return redirect(url_for('game'))
        else:
            flash("Failed to generate mission. Please try again.", "error")
            return redirect(url_for('character_selection'))
                             
    except Exception as e:
        logging.error(f"Error generating mission: {e}")
        flash("Failed to generate mission. Please try again.", "error")
        return redirect(url_for('character_selection'))

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

@app.route('/game', methods=['GET'])
def game():
    """Main game interface"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('start_game'))
        
        user_progress = UserProgress.query.filter_by(user_id=user_id).first()
        if not user_progress or not user_progress.current_node_id:
            return redirect(url_for('start_game'))
        
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
