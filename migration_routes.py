"""
Database Migration Routes
Author: Cascade

This module provides web endpoints for running database migrations
through the Flask app itself, avoiding psycopg2 installation issues.
"""

from flask import Blueprint, jsonify, request
from app import db
import logging

# Create blueprint for migration routes
migration_bp = Blueprint('migration', __name__, url_prefix='/admin/migration')

@migration_bp.route('/add_authenticated_user_id', methods=['POST'])
def add_authenticated_user_id_column():
    """Add the missing authenticated_user_id column to user_progress table"""
    
    try:
        # Check if column already exists
        result = db.session.execute(db.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_progress' 
            AND column_name = 'authenticated_user_id'
        """))
        
        if result.fetchone():
            return jsonify({
                'success': True,
                'message': 'Column authenticated_user_id already exists in user_progress table'
            })
        
        # Add the missing column
        logging.info("Adding missing authenticated_user_id column to user_progress table...")
        
        db.session.execute(db.text("""
            ALTER TABLE user_progress 
            ADD COLUMN authenticated_user_id INTEGER
        """))
        
        # Add the foreign key constraint
        db.session.execute(db.text("""
            ALTER TABLE user_progress 
            ADD CONSTRAINT fk_user_progress_authenticated_user 
            FOREIGN KEY (authenticated_user_id) REFERENCES users(id)
        """))
        
        db.session.commit()
        
        logging.info("Successfully added authenticated_user_id column!")
        
        return jsonify({
            'success': True,
            'message': 'Successfully added authenticated_user_id column to user_progress table'
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Migration error: {e}")
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@migration_bp.route('/status', methods=['GET'])
def migration_status():
    """Check the status of database schema"""
    
    try:
        # Check if authenticated_user_id column exists
        result = db.session.execute(db.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_progress' 
            AND column_name = 'authenticated_user_id'
        """))
        
        has_auth_column = result.fetchone() is not None
        
        return jsonify({
            'success': True,
            'schema_status': {
                'user_progress_has_authenticated_user_id': has_auth_column
            }
        })
        
    except Exception as e:
        logging.error(f"Status check error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
