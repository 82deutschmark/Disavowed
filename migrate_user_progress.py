#!/usr/bin/env python3
"""
User Progress Table Migration Script
Author: Cascade

This script adds the missing authenticated_user_id column to the user_progress table
using Flask-SQLAlchemy's built-in database operations.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_user_progress_table():
    """Add missing authenticated_user_id column using Flask-SQLAlchemy"""
    
    try:
        # Import our Flask app and database
        from app import app, db
        
        print("Starting user_progress table migration...")
        
        with app.app_context():
            # Check if the column already exists by trying to query it
            try:
                result = db.session.execute(db.text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_progress' AND column_name = 'authenticated_user_id'
                """))
                
                if result.fetchone():
                    print("✅ Column 'authenticated_user_id' already exists in user_progress table")
                    return True
                    
            except Exception as e:
                print(f"Error checking column existence: {e}")
            
            # Add the missing column using raw SQL
            try:
                print("Adding missing authenticated_user_id column...")
                db.session.execute(db.text("""
                    ALTER TABLE user_progress 
                    ADD COLUMN authenticated_user_id INTEGER REFERENCES users(id)
                """))
                
                # Commit the changes
                db.session.commit()
                print("✅ Successfully added authenticated_user_id column to user_progress table")
                return True
                
            except Exception as e:
                print(f"❌ Error adding column: {e}")
                db.session.rollback()
                return False
                
    except ImportError as e:
        print(f"❌ Error importing Flask app: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = migrate_user_progress_table()
    if success:
        print("\n🎉 Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
