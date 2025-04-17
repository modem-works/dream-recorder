import sqlite3
import os
import shutil
from datetime import datetime

def migrate_database():
    # Create a backup of the current database
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"dreams.db.pre_migration_{timestamp}"
    shutil.copy2("dreams.db", backup_name)
    print(f"Created backup of current database: {backup_name}")

    # Connect to both databases
    source_conn = sqlite3.connect("dreams.db.backup")
    target_conn = sqlite3.connect("dreams.db")
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()

    # Clear the current database
    target_cursor.execute("DELETE FROM dreams;")
    target_cursor.execute("DELETE FROM sqlite_sequence WHERE name='dreams';")

    # Get all records from the backup
    source_cursor.execute("""
        SELECT id, user_prompt, generated_prompt, audio_path, video_path, created_at, status
        FROM dreams
    """)
    records = source_cursor.fetchall()

    # Insert records into the new schema
    for record in records:
        # Convert paths to filenames
        audio_filename = os.path.basename(record[3]) if record[3] else None
        video_filename = os.path.basename(record[4]) if record[4] else None
        
        target_cursor.execute("""
            INSERT INTO dreams (
                id, user_prompt, generated_prompt, 
                audio_filename, video_filename, 
                created_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            record[0],  # id
            record[1],  # user_prompt
            record[2],  # generated_prompt
            audio_filename,
            video_filename,
            record[5],  # created_at
            record[6]   # status
        ))

    # Commit changes and close connections
    target_conn.commit()
    source_conn.close()
    target_conn.close()

    print("Migration completed successfully!")
    print(f"Migrated {len(records)} records from the backup database.")

if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        print("Please check the backup files and try again.") 