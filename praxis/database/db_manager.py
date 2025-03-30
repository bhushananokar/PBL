# praxis/database/db_manager.py
import os
import uuid
import hashlib
import datetime
import sqlite3
from typing import Optional, List, Dict, Tuple, Any

from config import DB_PATH, DEFAULT_SKILLS

class Database:
    """SQLite database for storing user data, challenges, and attempts."""
    
    def __init__(self, db_path=DB_PATH):
        """Initialize the database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        """Create necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # Programming languages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS programming_languages (
            lang_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
        ''')
        
        # Skills/concepts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            category TEXT
        )
        ''')
        
        # Challenges table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            challenge_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            enhanced_prompt TEXT,
            difficulty INTEGER,
            lang_id INTEGER,
            solution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lang_id) REFERENCES programming_languages(lang_id)
        )
        ''')
        
        # Challenge-skill mapping (many-to-many)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenge_skills (
            challenge_id TEXT,
            skill_id INTEGER,
            relevance REAL,
            PRIMARY KEY (challenge_id, skill_id),
            FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id),
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
        )
        ''')
        
        # User attempts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attempts (
            attempt_id TEXT PRIMARY KEY,
            user_id TEXT,
            challenge_id TEXT,
            code TEXT,
            feedback TEXT,
            score REAL,
            time_spent INTEGER,
            attempt_number INTEGER,
            successful BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id)
        )
        ''')
        
        # User skill proficiency table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_skills (
            user_id TEXT,
            skill_id INTEGER,
            proficiency REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, skill_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
        )
        ''')
        
        # User preferences table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id TEXT PRIMARY KEY,
            difficulty_preference INTEGER,
            theme TEXT,
            preferences JSON,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Learning paths table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_paths (
            path_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            difficulty INTEGER,
            lang_id INTEGER,
            ordering JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lang_id) REFERENCES programming_languages(lang_id)
        )
        ''')
        
        # Learning path items
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_path_items (
            path_id TEXT,
            challenge_id TEXT,
            position INTEGER,
            PRIMARY KEY (path_id, challenge_id),
            FOREIGN KEY (path_id) REFERENCES learning_paths(path_id),
            FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id)
        )
        ''')
        
        # Populate programming languages
        langs = ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "TypeScript", "Rust", "Swift", "Kotlin"]
        for lang in langs:
            cursor.execute('INSERT OR IGNORE INTO programming_languages (name) VALUES (?)', (lang,))
        
        # Populate skills/concepts with common programming concepts
        for skill_name, category in DEFAULT_SKILLS:
            cursor.execute('INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)', (skill_name, category))
        
        self.conn.commit()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    # User management methods
    def create_user(self, username: str, password: str, email: Optional[str] = None) -> Optional[str]:
        """Create a new user in the database."""
        user_id = str(uuid.uuid4())
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        current_time = datetime.datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (user_id, username, password_hash, email, created_at, last_login) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, username, password_hash, email, current_time, current_time)
            )
            self.conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate a user."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE username = ? AND password_hash = ?', (username, password_hash))
        user = cursor.fetchone()
        
        if user:
            # Update last login time
            current_time = datetime.datetime.now().isoformat()
            cursor.execute('UPDATE users SET last_login = ? WHERE user_id = ?', (current_time, user[0]))
            self.conn.commit()
            return user[0]
        
        return None
    
    # Challenge management methods
    def store_challenge(self, problem_desc: str, enhanced_prompt: str, language: str, difficulty: int = 2) -> Optional[str]:
        """Store a new coding challenge in the database."""
        challenge_id = str(uuid.uuid4())
        
        # Get language ID
        cursor = self.conn.cursor()
        cursor.execute('SELECT lang_id FROM programming_languages WHERE name = ?', (language,))
        lang_result = cursor.fetchone()
        if not lang_result:
            return None
        
        lang_id = lang_result[0]
        
        cursor.execute(
            'INSERT INTO challenges (challenge_id, title, description, enhanced_prompt, difficulty, lang_id) VALUES (?, ?, ?, ?, ?, ?)',
            (challenge_id, problem_desc[:50], problem_desc, enhanced_prompt, difficulty, lang_id)
        )
        self.conn.commit()
        return challenge_id
    
    def update_challenge_solution(self, challenge_id: str, solution: str) -> None:
        """Update the solution for a challenge."""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE challenges SET solution = ? WHERE challenge_id = ?', (solution, challenge_id))
        self.conn.commit()
    
    def map_challenge_skills(self, challenge_id: str, skill_relevance: Dict[str, float]) -> None:
        """Map a challenge to relevant skills with relevance scores."""
        cursor = self.conn.cursor()
        for skill_name, relevance in skill_relevance.items():
            # Get skill ID or create if it doesn't exist
            cursor.execute('SELECT skill_id FROM skills WHERE name = ?', (skill_name,))
            skill_result = cursor.fetchone()
            if not skill_result:
                cursor.execute('INSERT INTO skills (name, category) VALUES (?, ?)', (skill_name, "auto_detected"))
                self.conn.commit()
                cursor.execute('SELECT skill_id FROM skills WHERE name = ?', (skill_name,))
                skill_result = cursor.fetchone()
            
            skill_id = skill_result[0]
            
            # Map challenge to skill
            cursor.execute(
                'INSERT OR REPLACE INTO challenge_skills (challenge_id, skill_id, relevance) VALUES (?, ?, ?)',
                (challenge_id, skill_id, relevance)
            )
        self.conn.commit()
    
    # User attempt methods
    def store_attempt(self, user_id: str, challenge_id: str, code: str, feedback: str, 
                     score: float, time_spent: int, attempt_number: int, successful: bool = False) -> str:
        """Store a user's attempt at a challenge."""
        attempt_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO attempts (attempt_id, user_id, challenge_id, code, feedback, score, time_spent, attempt_number, successful) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (attempt_id, user_id, challenge_id, code, feedback, score, time_spent, attempt_number, successful)
        )
        self.conn.commit()
        return attempt_id
    
    def update_user_skills(self, user_id: str, challenge_id: str, score: float) -> None:
        """Update user's skill proficiency based on a challenge attempt."""
        cursor = self.conn.cursor()
        
        # Get skills related to the challenge
        cursor.execute('''
            SELECT s.skill_id, s.name, cs.relevance
            FROM challenge_skills cs
            JOIN skills s ON cs.skill_id = s.skill_id
            WHERE cs.challenge_id = ?
        ''', (challenge_id,))
        
        challenge_skills = cursor.fetchall()
        
        for skill_id, skill_name, relevance in challenge_skills:
            # Check if user already has this skill
            cursor.execute('SELECT proficiency FROM user_skills WHERE user_id = ? AND skill_id = ?', (user_id, skill_id))
            current_proficiency = cursor.fetchone()
            
            if current_proficiency:
                # Update existing proficiency
                # Formula: new_prof = (old_prof * 0.7) + (attempt_score * relevance * 0.3)
                new_proficiency = (current_proficiency[0] * 0.7) + (score * relevance * 0.3)
                cursor.execute(
                    'UPDATE user_skills SET proficiency = ?, last_updated = ? WHERE user_id = ? AND skill_id = ?',
                    (new_proficiency, datetime.datetime.now().isoformat(), user_id, skill_id)
                )
            else:
                # Create new skill proficiency entry
                cursor.execute(
                    'INSERT INTO user_skills (user_id, skill_id, proficiency) VALUES (?, ?, ?)',
                    (user_id, skill_id, score * relevance)
                )
        
        self.conn.commit()
    
    # User skill methods
    def get_user_skills(self, user_id: str) -> List[Tuple]:
        """Get a user's skill proficiencies."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.skill_id, s.name, s.category, us.proficiency
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.skill_id
            WHERE us.user_id = ?
            ORDER BY us.proficiency DESC
        ''', (user_id,))
        
        return cursor.fetchall()
    
    def get_user_weakest_skills(self, user_id: str, limit: int = 5) -> List[Tuple]:
        """Get a user's weakest skills."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.skill_id, s.name, s.category, us.proficiency
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.skill_id
            WHERE us.user_id = ?
            ORDER BY us.proficiency ASC
            LIMIT ?
        ''', (user_id, limit))
        
        return cursor.fetchall()
    
    def get_user_strongest_skills(self, user_id: str, limit: int = 5) -> List[Tuple]:
        """Get a user's strongest skills."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.skill_id, s.name, s.category, us.proficiency
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.skill_id
            WHERE us.user_id = ?
            ORDER BY us.proficiency DESC
            LIMIT ?
        ''', (user_id, limit))
        
        return cursor.fetchall()
    
    # Recommendation methods
    def get_recommended_challenges(self, user_id: str, limit: int = 5) -> List[Tuple]:
        """Get personalized challenge recommendations for a user."""
        cursor = self.conn.cursor()
        
        # Get weakest skills
        weak_skills = self.get_user_weakest_skills(user_id, limit=3)
        weak_skill_ids = [skill[0] for skill in weak_skills]
        
        if not weak_skill_ids:
            return []
        
        # Get challenges that target these weak skills but haven't been attempted by the user
        placeholders = ', '.join(['?' for _ in weak_skill_ids])
        
        cursor.execute(f'''
            SELECT c.challenge_id, c.title, c.description, c.difficulty, pl.name as language, 
                   GROUP_CONCAT(s.name) as skills
            FROM challenges c
            JOIN programming_languages pl ON c.lang_id = pl.lang_id
            JOIN challenge_skills cs ON c.challenge_id = cs.challenge_id
            JOIN skills s ON cs.skill_id = s.skill_id
            WHERE cs.skill_id IN ({placeholders})
            AND c.challenge_id NOT IN (
                SELECT challenge_id FROM attempts WHERE user_id = ?
            )
            GROUP BY c.challenge_id
            ORDER BY c.difficulty ASC
            LIMIT ?
        ''', (*weak_skill_ids, user_id, limit))
        
        return cursor.fetchall()
    
    # User progress methods
    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get a user's overall progress statistics."""
        cursor = self.conn.cursor()
        
        # Get total attempts and successful attempts
        cursor.execute('''
            SELECT COUNT(*) as total_attempts,
                   SUM(CASE WHEN successful = 1 THEN 1 ELSE 0 END) as successful_attempts,
                   COUNT(DISTINCT challenge_id) as challenges_attempted
            FROM attempts
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        # Get average score
        cursor.execute('''
            SELECT AVG(score) as average_score
            FROM attempts
            WHERE user_id = ?
        ''', (user_id,))
        
        avg_score = cursor.fetchone()
        
        return {
            'total_attempts': result[0] if result[0] else 0,
            'successful_attempts': result[1] if result[1] else 0,
            'challenges_attempted': result[2] if result[2] else 0,
            'average_score': avg_score[0] if avg_score[0] else 0
        }
    
    def get_user_recent_attempts(self, user_id: str, limit: int = 5) -> List[Tuple]:
        """Get a user's recent challenge attempts."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.attempt_id, a.challenge_id, c.title, a.score, a.attempt_number, a.successful, a.created_at
            FROM attempts a
            JOIN challenges c ON a.challenge_id = c.challenge_id
            WHERE a.user_id = ?
            ORDER BY a.created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        return cursor.fetchall()
    
    def get_skill_progress_over_time(self, user_id: str, skill_id: int) -> List[Tuple]:
        """Get a user's progress in a specific skill over time."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.created_at, a.score, cs.relevance
            FROM attempts a
            JOIN challenge_skills cs ON a.challenge_id = cs.challenge_id
            WHERE a.user_id = ? AND cs.skill_id = ?
            ORDER BY a.created_at ASC
        ''', (user_id, skill_id))
        
        return cursor.fetchall()
    
    # Learning path methods
    def get_or_create_learning_path(self, title: str, description: str, language: str, difficulty: int = 2) -> str:
        """Get or create a learning path."""
        cursor = self.conn.cursor()
        
        # Check if path already exists
        cursor.execute('SELECT path_id FROM learning_paths WHERE title = ? AND lang_id = (SELECT lang_id FROM programming_languages WHERE name = ?)',
                      (title, language))
        path = cursor.fetchone()
        
        if path:
            return path[0]
        
        # Create new path
        path_id = str(uuid.uuid4())
        
        # Get language ID
        cursor.execute('SELECT lang_id FROM programming_languages WHERE name = ?', (language,))
        lang_id = cursor.fetchone()[0]
        
        cursor.execute(
            'INSERT INTO learning_paths (path_id, title, description, difficulty, lang_id, ordering) VALUES (?, ?, ?, ?, ?, ?)',
            (path_id, title, description, difficulty, lang_id, '[]')
        )
        self.conn.commit()
        return path_id
    
    def add_challenge_to_path(self, path_id: str, challenge_id: str, position: int) -> None:
        """Add a challenge to a learning path."""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO learning_path_items (path_id, challenge_id, position) VALUES (?, ?, ?)',
            (path_id, challenge_id, position)
        )
        self.conn.commit()
    
    def get_learning_path_challenges(self, path_id: str) -> List[Tuple]:
        """Get all challenges in a learning path, ordered by position."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.challenge_id, c.title, c.description, c.difficulty, pl.name as language
            FROM learning_path_items lpi
            JOIN challenges c ON lpi.challenge_id = c.challenge_id
            JOIN programming_languages pl ON c.lang_id = pl.lang_id
            WHERE lpi.path_id = ?
            ORDER BY lpi.position ASC
        ''', (path_id,))
        
        return cursor.fetchall()
    
    # Skill analysis methods
    def get_skill_analysis(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get comprehensive skill analysis for a user."""
        # Get all skills with proficiency
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.skill_id, s.name, s.category, COALESCE(us.proficiency, 0) as proficiency,
                  (SELECT COUNT(*) FROM attempts a 
                   JOIN challenge_skills cs ON a.challenge_id = cs.challenge_id 
                   WHERE a.user_id = ? AND cs.skill_id = s.skill_id) as practice_count
            FROM skills s
            LEFT JOIN user_skills us ON s.skill_id = us.skill_id AND us.user_id = ?
            ORDER BY proficiency DESC
        ''', (user_id, user_id))
        
        skills = cursor.fetchall()
        
        # Group by category
        categories = {}
        for skill in skills:
            skill_id, name, category, proficiency, practice_count = skill
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                'skill_id': skill_id,
                'name': name,
                'proficiency': proficiency,
                'practice_count': practice_count
            })
        
        return categories