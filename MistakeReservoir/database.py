import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "reservoir.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Sources
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_date TEXT
            )
        ''')
        
        # Materials (Shared content for Data Analysis etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                content_html TEXT,
                images TEXT, -- JSON List
                type TEXT
            )
        ''')
        
        # Questions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                material_id INTEGER,
                original_num INTEGER,
                type TEXT,
                content_html TEXT,
                options_html TEXT, -- Separated Options
                answer_html TEXT, -- Analysis + Answer
                images TEXT, -- JSON List
                FOREIGN KEY(source_id) REFERENCES sources(id),
                FOREIGN KEY(material_id) REFERENCES materials(id)
            )
        ''')
        
        # Review Stats (The Reservoir State)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_stats (
                question_id INTEGER PRIMARY KEY,
                status TEXT DEFAULT 'pool', -- pool, archived
                mistake_count INTEGER DEFAULT 1,
                last_wrong_date TEXT,
                last_right_date TEXT,
                FOREIGN KEY(question_id) REFERENCES questions(id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_source(self, filename: str) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO sources (filename, upload_date) VALUES (?, ?)", 
                  (filename, datetime.now().isoformat()))
        sid = c.lastrowid
        conn.commit()
        conn.close()
        return sid

    def add_material(self, source_id: int, content: str, images: List[str] = [], type: str = "data_analysis") -> int:
        # Check duplicate? (Simple check by content hash or just text matching if needed, 
        # but here we allow dupes if from different imports or relying on source_id)
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO materials (source_id, content_html, images, type) VALUES (?, ?, ?, ?)",
                  (source_id, content, json.dumps(images), type))
        mid = c.lastrowid
        conn.commit()
        conn.close()
        return mid

    def add_question(self, source_id: int, original_num: int, content: str, options: str,
                     answer: str, images: List[str], type: str, material_id: Optional[int] = None) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        
        # Check existence?
        c.execute("SELECT id FROM questions WHERE source_id=? AND original_num=?", (source_id, original_num))
        exist = c.fetchone()
        if exist:
            qid = exist['id']
            # Update content
            c.execute('''
                UPDATE questions 
                SET content_html=?, options_html=?, answer_html=?, images=?, type=?, material_id=?
                WHERE id=?
            ''', (content, options, answer, json.dumps(images), type, material_id, qid))
            conn.commit()
            conn.close()
            return qid
            
        c.execute('''
            INSERT INTO questions (source_id, material_id, original_num, type, content_html, options_html, answer_html, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (source_id, material_id, original_num, type, content, options, answer, json.dumps(images)))
        
        qid = c.lastrowid
        
        # Init Stats
        c.execute('''
            INSERT INTO review_stats (question_id, status, last_wrong_date)
            VALUES (?, 'pool', ?)
        ''', (qid, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return qid

    def get_pool_status(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT q.type, COUNT(*) as count 
            FROM review_stats r
            JOIN questions q ON r.question_id = q.id
            WHERE r.status = 'pool'
            GROUP BY q.type
        ''')
        stats = {row['type']: row['count'] for row in c.fetchall()}
        conn.close()
        return stats

    def get_random_questions(self, count: int, type_filter: List[str] = None):
        """
        Fetch random questions from the pool.
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        query = '''
            SELECT q.*, m.content_html as material_content, m.images as material_images
            FROM review_stats r
            JOIN questions q ON r.question_id = q.id
            LEFT JOIN materials m ON q.material_id = m.id
            WHERE r.status = 'pool'
        '''
        params = []
        
        if type_filter:
            placeholders = ','.join(['?'] * len(type_filter))
            query += f" AND q.type IN ({placeholders})"
            params.extend(type_filter)
            
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(count)
        
        c.execute(query, params)
        rows = c.fetchall()
        
        # Convert to dict
        questions = []
        for row in rows:
            q = dict(row)
            # Parse JSONs
            if q.get('images'): q['images'] = json.loads(q['images'])
            if q.get('material_images'): q['material_images'] = json.loads(q['material_images'])
            questions.append(q)
            
        conn.close()
        return questions

if __name__ == "__main__":
    db = DatabaseManager("test.db")
    print("DB Initialized")
