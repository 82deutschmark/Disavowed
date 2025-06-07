from app import db
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    google_id = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    profile_pic = Column(String(200))
    diamonds = Column(Integer, default=50)  # All users start with 50 diamonds
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to user progress
    progress = relationship("UserProgress", back_populates="authenticated_user", uselist=False)

class Currency(db.Model):
    __tablename__ = 'currency'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    symbol = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    __tablename__ = 'transaction'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    from_currency = Column(String(10))
    to_currency = Column(String(10))
    amount = Column(Integer, nullable=False)
    description = Column(Text)
    story_node_id = Column(Integer, ForeignKey('story_node.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

class Character(db.Model):
    __tablename__ = 'characters'
    
    id = Column(Integer, primary_key=True)
    image_url = Column(String(500))
    character_name = Column(String(200), nullable=False)
    character_traits = Column(JSON)
    character_role = Column(String(100))
    plot_lines = Column(JSON)
    backstory = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SceneImages(db.Model):
    __tablename__ = 'scene_images'
    
    id = Column(Integer, primary_key=True)
    image_url = Column(String(500))
    image_width = Column(Integer)
    image_height = Column(Integer)
    image_format = Column(String(10))
    image_size_bytes = Column(Integer)
    image_type = Column(String(50), default='scene')
    analysis_result = Column(JSON)
    name = Column(String(200))
    scene_type = Column(String(100))
    setting = Column(String(500))
    setting_description = Column(Text)
    story_fit = Column(JSON)
    dramatic_moments = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class StoryGeneration(db.Model):
    __tablename__ = 'story_generation'
    
    id = Column(Integer, primary_key=True)
    primary_conflict = Column(Text)
    setting = Column(String(500))
    narrative_style = Column(String(100))
    mood = Column(String(100))
    generated_story = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class StoryNode(db.Model):
    __tablename__ = 'story_node'
    
    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey('story_generation.id'))
    narrative_text = Column(Text, nullable=False)
    character_id = Column(Integer, ForeignKey('characters.id'))
    is_endpoint = Column(Boolean, default=False)
    parent_node_id = Column(Integer, ForeignKey('story_node.id'))
    achievement_id = Column(Integer, ForeignKey('achievement.id'))
    branch_metadata = Column(JSON)
    generated_by_ai = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    story = relationship("StoryGeneration", backref="nodes")
    character = relationship("Character", backref="story_nodes")
    choices = relationship("StoryChoice", back_populates="node", foreign_keys="StoryChoice.node_id")

class StoryChoice(db.Model):
    __tablename__ = 'story_choice'
    
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey('story_node.id'), nullable=False)
    choice_text = Column(Text, nullable=False)
    next_node_id = Column(Integer, ForeignKey('story_node.id'))
    currency_requirements = Column(JSON)
    choice_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node = relationship("StoryNode", back_populates="choices", foreign_keys=[node_id])
    next_node = relationship("StoryNode", foreign_keys=[next_node_id])

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False, unique=True)  # Keep for guest sessions
    authenticated_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Link to authenticated users
    current_node_id = Column(Integer, ForeignKey('story_node.id'))
    current_story_id = Column(Integer, ForeignKey('story_generation.id'))
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    choice_history = Column(JSON, default=list)
    achievements_earned = Column(JSON, default=list)
    currency_balances = Column(JSON, default=lambda: {"💎": 50, "💵": 50, "💷": 40, "💶": 45, "💴": 500})  # Start with 50 diamonds
    encountered_characters = Column(JSON, default=list)
    active_missions = Column(JSON, default=list)
    completed_missions = Column(JSON, default=list)
    failed_missions = Column(JSON, default=list)
    active_plot_arcs = Column(JSON, default=list)
    completed_plot_arcs = Column(JSON, default=list)
    game_state = Column(JSON, default=dict)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    current_node = relationship("StoryNode", foreign_keys=[current_node_id])
    current_story = relationship("StoryGeneration", foreign_keys=[current_story_id])
    authenticated_user = relationship("User", foreign_keys=[authenticated_user_id])

class Mission(db.Model):
    __tablename__ = 'mission'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    giver_id = Column(Integer, ForeignKey('characters.id'))
    target_id = Column(Integer, ForeignKey('characters.id'))
    objective = Column(Text)
    status = Column(String(50), default='active')
    difficulty = Column(String(20))
    reward_currency = Column(String(10))
    reward_amount = Column(Integer)
    deadline = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    story_id = Column(Integer, ForeignKey('story_generation.id'))
    progress = Column(Integer, default=0)
    progress_updates = Column(JSON, default=list)
    
    # Relationships
    giver = relationship("Character", foreign_keys=[giver_id])
    target = relationship("Character", foreign_keys=[target_id])
    story = relationship("StoryGeneration")

class Achievement(db.Model):
    __tablename__ = 'achievement'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    criteria = Column(JSON)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class PlotArc(db.Model):
    __tablename__ = 'plot_arc'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    arc_type = Column(String(50))
    story_id = Column(Integer, ForeignKey('story_generation.id'))
    status = Column(String(50))
    completion_criteria = Column(JSON)
    progress_markers = Column(JSON)
    key_nodes = Column(JSON)
    branching_choices = Column(JSON)
    primary_characters = Column(JSON)
    rewards = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    story = relationship("StoryGeneration")

class AIInstruction(db.Model):
    __tablename__ = 'ai_instruction'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    prompt_template = Column(Text)
    parameters = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
