import sqlite3
import json
from datetime import datetime
from pathlib import Path
import logging
from pydantic import BaseModel
from typing import Optional
import os

logger = logging.getLogger(__name__)

class DreamData(BaseModel):
    user_prompt: str
    generated_prompt: str
    audio_filename: str
    video_filename: str
    thumb_filename: Optional[str] = None
    status: Optional[str] = 'completed'

class DreamDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.getenv('DREAMS_DB_PATH', '/app/db/dreams.db')
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dreams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_prompt TEXT NOT NULL,
                    generated_prompt TEXT NOT NULL,
                    audio_filename TEXT NOT NULL,
                    video_filename TEXT NOT NULL,
                    thumb_filename TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT
                )
            ''')
            conn.commit()
    
    def save_dream(self, dream_data):
        """Save a new dream record to the database."""
        required_fields = ['user_prompt', 'generated_prompt', 'audio_filename', 'video_filename']
        for field in required_fields:
            if field not in dream_data:
                raise ValueError(f"Missing required field: {field}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dreams (
                    user_prompt, generated_prompt, audio_filename, video_filename,
                    thumb_filename, status
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                dream_data['user_prompt'],
                dream_data['generated_prompt'],
                dream_data['audio_filename'],
                dream_data['video_filename'],
                dream_data.get('thumb_filename'),
                dream_data.get('status', 'completed')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_dream(self, dream_id):
        """Get a single dream by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM dreams WHERE id = ?', (dream_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None
    
    def get_all_dreams(self):
        """Get all dreams, ordered by creation date (newest first)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM dreams ORDER BY created_at DESC')
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def update_dream(self, dream_id, updates):
        """Update an existing dream."""
        if not updates:
            return
        
        try:
            set_clauses = []
            values = []
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(dream_id)
            query = f"UPDATE dreams SET {', '.join(set_clauses)} WHERE id = ?"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(query, values)
                    conn.commit()
                    return cursor.rowcount > 0
                except sqlite3.Error as e:
                    if logger:
                        logger.error(f"Database error: {str(e)}")
                    if logger:
                        logger.error(f"Query: {query}")
                    if logger:
                        logger.error(f"Values: {values}")
                    raise
        except Exception as e:
            if logger:
                logger.error(f"Error updating dream {dream_id}: {str(e)}")
            raise
    
    def delete_dream(self, dream_id):
        """Delete a dream from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM dreams WHERE id = ?', (dream_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def _row_to_dict(self, row):
        """Convert a database row to a dictionary."""
        return dict(row) 