#!/usr/bin/env python3
"""
Fix User Progress Table Migration
Author: Cascade

This script adds the missing authenticated_user_id column to the user_progress table.
The column exists in the model but not in the actual database table.
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_user_progress_table():
    """Add missing authenticated_user_id column to user_progress table"""
    
    # Database connection string
    db_url = "postgresql+psycopg2://neondb_owner:npg_H4GPNkYFlg7C@ep-lingering-silence-a5emvgcs.us-east-2.aws.neon.tech/neondb?sslmode=require"
    
    # Extract connection params from URL
    # For psycopg2, we need to convert the URL format
    conn_params = {
        'host': 'ep-lingering-silence-a5emvgcs.us-east-2.aws.neon.tech',
        'database': 'neondb',
        'user': 'neondb_owner',
        'password': 'npg_H4GPNkYFlg7C',
        'sslmode': 'require'
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_progress' AND column_name = 'authenticated_user_id'
        """)
        
        if cursor.fetchone():
            print("Column 'authenticated_user_id' already exists in user_progress table")
            return
        
        # Add the missing column
        print("Adding missing authenticated_user_id column to user_progress table...")
        cursor.execute("""
            ALTER TABLE user_progress 
            ADD COLUMN authenticated_user_id INTEGER REFERENCES users(id)
        """)
        
        # Commit the changes
        conn.commit()
        print("✅ Successfully added authenticated_user_id column to user_progress table")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_user_progress_table()
