"""
DrCodePT Phase 7 - SQLite Database Module
Persistent storage for study sessions, cards, and progress
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class DrCodePTDatabase:
    """Database handler for persistent state"""
    
    DB_PATH = Path(__file__).parent / "drcodept.db"
    
    def __init__(self):
        self.db_path = self.DB_PATH
        self.init_db()
    
    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                due_dates INTEGER DEFAULT 0,
                anki_cards INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Study sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL,
                topic TEXT,
                cards_generated INTEGER,
                cards_added_to_anki INTEGER,
                quiz_score INTEGER,
                duration_minutes INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(course_id) REFERENCES courses(id)
            )
        ''')
        
        # Cards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                course_id TEXT,
                front TEXT,
                back TEXT,
                tags TEXT,
                deck_name TEXT,
                added_to_anki BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES study_sessions(id),
                FOREIGN KEY(course_id) REFERENCES courses(id)
            )
        ''')
        
        # Dashboard stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dashboard_stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_cards INTEGER DEFAULT 0,
                total_study_sessions INTEGER DEFAULT 0,
                total_study_time_minutes INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize default courses if not exists
        courses = [
            ('legal', 'Legal & Ethics', 14, 45),
            ('lifespan', 'Lifespan Development', 2, 12),
            ('pathology', 'Clinical Pathology', 22, 89),
            ('anatomy', 'Anatomy', 6, 120),
            ('exam_skills', 'Exam Skills', 4, 15),
        ]
        
        for course_id, name, due_dates, anki_cards in courses:
            cursor.execute('''
                INSERT OR IGNORE INTO courses (id, name, due_dates, anki_cards)
                VALUES (?, ?, ?, ?)
            ''', (course_id, name, due_dates, anki_cards))
        
        # Initialize dashboard stats if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO dashboard_stats (id, total_cards)
            VALUES (1, (SELECT SUM(anki_cards) FROM courses))
        ''')
        
        conn.commit()
        conn.close()
    
    def get_dashboard_state(self) -> Dict:
        """Get current dashboard state from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get courses
        cursor.execute('SELECT id, name, due_dates, anki_cards FROM courses ORDER BY name')
        courses = [dict(row) for row in cursor.fetchall()]
        
        # Get stats
        cursor.execute('SELECT total_cards, total_study_sessions, total_study_time_minutes FROM dashboard_stats WHERE id = 1')
        stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'courses': courses,
            'total_cards': stats['total_cards'] if stats else 0,
            'study_sessions': stats['total_study_sessions'] if stats else 0,
            'total_study_time': stats['total_study_time_minutes'] if stats else 0,
        }
    
    def add_study_session(self, course_id: str, topic: str, cards_generated: int, 
                          cards_added: int, quiz_score: int = 0, duration_minutes: int = 45) -> int:
        """Add a study session and return session_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO study_sessions 
            (course_id, topic, cards_generated, cards_added_to_anki, quiz_score, duration_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (course_id, topic, cards_generated, cards_added, quiz_score, duration_minutes))
        
        session_id = cursor.lastrowid
        
        # Update dashboard stats
        cursor.execute('''
            UPDATE dashboard_stats
            SET total_cards = total_cards + ?,
                total_study_sessions = total_study_sessions + 1,
                total_study_time_minutes = total_study_time_minutes + ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE id = 1
        ''', (cards_added, duration_minutes))
        
        # Update course card count
        cursor.execute('''
            UPDATE courses
            SET anki_cards = anki_cards + ?
            WHERE id = ?
        ''', (cards_added, course_id))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def add_cards(self, session_id: int, course_id: str, cards: List[Dict], deck_name: str) -> int:
        """Add cards to database and return count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        added_count = 0
        for card in cards:
            try:
                cursor.execute('''
                    INSERT INTO cards (session_id, course_id, front, back, tags, deck_name, added_to_anki)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (
                    session_id,
                    course_id,
                    card.get('front', ''),
                    card.get('back', ''),
                    json.dumps(card.get('tags', [])),
                    deck_name
                ))
                added_count += 1
            except Exception as e:
                print(f"Error adding card: {e}")
        
        conn.commit()
        conn.close()
        
        return added_count
    
    def get_study_history(self, course_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get study history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if course_id:
            cursor.execute('''
                SELECT id, course_id, topic, cards_generated, cards_added_to_anki, 
                       quiz_score, duration_minutes, timestamp
                FROM study_sessions
                WHERE course_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (course_id, limit))
        else:
            cursor.execute('''
                SELECT id, course_id, topic, cards_generated, cards_added_to_anki, 
                       quiz_score, duration_minutes, timestamp
                FROM study_sessions
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return sessions
    
    def get_course_cards(self, course_id: str, limit: int = 100) -> List[Dict]:
        """Get cards for a course"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, front, back, tags, deck_name, created_at
            FROM cards
            WHERE course_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (course_id, limit))
        
        cards = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return cards
    
    def get_stats(self) -> Dict:
        """Get aggregate statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                SUM(anki_cards) as total_cards,
                COUNT(*) as total_courses
            FROM courses
        ''')
        course_stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sessions,
                SUM(duration_minutes) as total_time,
                AVG(quiz_score) as avg_score
            FROM study_sessions
        ''')
        session_stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) as total_cards_added FROM cards WHERE added_to_anki = 1
        ''')
        card_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_cards': course_stats['total_cards'] or 0,
            'total_courses': course_stats['total_courses'] or 0,
            'total_study_sessions': session_stats['total_sessions'] or 0,
            'total_study_time_minutes': session_stats['total_time'] or 0,
            'average_quiz_score': session_stats['avg_score'] or 0,
            'total_cards_added_to_anki': card_stats['total_cards_added'] or 0,
        }


def get_db() -> DrCodePTDatabase:
    """Get database instance"""
    return DrCodePTDatabase()
