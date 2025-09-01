#!/usr/bin/env python3
"""
Simple script to view the last 5 client inputs from the database.
Run with: python view_history.py
"""

import sqlite3
import os
from datetime import datetime

def view_recent_inputs(db_path="./client_history.db", limit=5):
    """View the most recent client inputs from the database"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("   Make sure the agent has been run at least once to create the database.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM client_inputs')
        total_count = cursor.fetchone()[0]
        
        # Get recent inputs
        cursor.execute('''
            SELECT id, input_text, timestamp, session_id, user_id
            FROM client_inputs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        print("=" * 80)
        print(f"📋 RECENT CLIENT INPUTS (Last {len(results)} of {total_count} total)")
        print("=" * 80)
        
        if not results:
            print("   No inputs found in database.")
            return
        
        for i, (id, input_text, timestamp, session_id, user_id) in enumerate(results, 1):
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = timestamp or "Unknown"
            
            print(f"\n{i}. ID: {id}")
            print(f"   Time: {time_str}")
            print(f"   User: {user_id}")
            if session_id:
                print(f"   Session: {session_id}")
            print(f"   Input: {input_text}")
            print("-" * 60)
        
        print(f"\n💾 Database: {db_path}")
        print(f"📊 Total entries: {total_count}")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("Client Input History Viewer")
    print("=" * 40)
    
    # Check if custom database path provided
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        print(f"Using custom database: {db_path}")
    else:
        db_path = "./client_history.db"
    
    view_recent_inputs(db_path)

if __name__ == "__main__":
    main()
