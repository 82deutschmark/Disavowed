#!/usr/bin/env python3
"""
Database Migration Runner
Author: Cascade

This script runs database migrations using the existing Flask app context,
avoiding the need for separate psycopg2 installation.
"""

import os
import sys

def run_migration():
    """Run database migration using Flask app context"""
    
    try:
        # Import our Flask app
        from app import app, db
        
        print("🔧 Starting database migration...")
        
        with app.app_context():
            try:
                # Check if authenticated_user_id column exists
                result = db.session.execute(db.text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_progress' 
                    AND column_name = 'authenticated_user_id'
                """))
                
                if result.fetchone():
                    print("✅ Column 'authenticated_user_id' already exists")
                    return True
                
                print("➕ Adding missing authenticated_user_id column...")
                
                # Add the missing column
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
                print("✅ Successfully added authenticated_user_id column!")
                return True
                
            except Exception as e:
                print(f"❌ Migration error: {e}")
                db.session.rollback()
                return False
                
    except Exception as e:
        print(f"❌ App initialization error: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("🎉 Migration completed!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
