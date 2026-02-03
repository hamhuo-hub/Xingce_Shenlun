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
        
        # Check if source exists to prevent duplication
        c.execute("SELECT id FROM sources WHERE filename=?", (filename,))
        row = c.fetchone()
        
        if row:
            sid = row['id']
            # Update upload date to reflect recent activity
            c.execute("UPDATE sources SET upload_date=? WHERE id=?", 
                      (datetime.now().isoformat(), sid))
        else:
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

    def get_standard_exam_questions(self, count: int = 130):
        """
        Fetch questions respecting the standard composition:
        Common: 20
        Verbal: 40
        Quant: 15
        Judgment: 40 (Graph 10, Dict 10, Analogy 10, Logic 10)
        Data: 15
        
        If count != 130, we scale these ratios.
        """
        SCALE = count / 130.0
        
        # Define Composition
        # Using exact matching for types stored in DB
        
        # Note: In DB, '判断' might be stored as specific subtypes '图形', '定义', '类比', '逻辑'
        # based on extractor logic if section headers were found.
        # However, extractor defaults to '判断' if only "判断" found.
        # We need to handle fallback.
        
        composition = [
            ("常识", int(20 * SCALE)),
            ("言语", int(40 * SCALE)),
            ("数量", int(15 * SCALE)),
            ("资料", int(15 * SCALE)),
            # Judyment Subtypes
            ("图形", int(10 * SCALE)),
            ("定义", int(10 * SCALE)),
            ("类比", int(10 * SCALE)),
            ("逻辑", int(10 * SCALE)),
        ]
        
        all_questions = []
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row # Ensure we get dict-like access
        
        # Fetch for each type
        for type_key, needed in composition:
            if needed <= 0: continue
            
            # For Judgment subtypes, we query specifically.
            # But what if DB has just "判断"? 
            # We add a fallback: if specific subtypes yield 0, try fetching "判断" and distribute?
            # For now, simplistic approach:
            
            c = conn.cursor()
            # Select with limit
            # Also join materials
            query = '''
                SELECT q.*, m.content_html as material_content, m.images as material_images
                FROM review_stats r
                JOIN questions q ON r.question_id = q.id
                LEFT JOIN materials m ON q.material_id = m.id
                WHERE r.status = 'pool' AND q.type LIKE ?
                ORDER BY RANDOM() LIMIT ?
            '''
            c.execute(query, (f"%{type_key}%", needed))
            rows = c.fetchall()
            
            for row in rows:
                q = dict(row)
                if q.get('images'): q['images'] = json.loads(q['images'])
                if q.get('material_images'): q['material_images'] = json.loads(q['material_images'])
                all_questions.append(q)
                
            c.close()

        conn.close()
        
        # If we are short on questions (e.g. didn't find "图形" but only "判断"), 
        # we currently just return what we found. 
        # Ideally we should fill gaps with "Unknown" or generic "判断" if subtypes missing.
        
        return all_questions

    def wipe_database(self):
        """
        Wipe all data from tables but keep the schema.
        """
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute("DELETE FROM review_stats")
            c.execute("DELETE FROM questions")
            c.execute("DELETE FROM materials")
            c.execute("DELETE FROM sources")
            conn.commit()
            print("Database Wiped Clean.")
        except Exception as e:
            print(f"Error wiping database: {e}")
            conn.rollback()
        finally:
            conn.close()

    def migrate_database(self):
        """
        Run schema migrations.
        """
        conn = self.get_connection()
        c = conn.cursor()
        try:
            # Migration 1: Add options_html if missing
            try:
                c.execute("ALTER TABLE questions ADD COLUMN options_html TEXT")
                print("Added options_html column.")
            except sqlite3.OperationalError:
                pass # Already exists

            conn.commit()
            print("Migration checks completed.")
        except Exception as e:
            print(f"Error migrating database: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Manager CLI")
    parser.add_argument("--wipe", action="store_true", help="Wipe all data from database")
    parser.add_argument("--migrate", action="store_true", help="Run schema migrations")
    
    args = parser.parse_args()
    
    db = DatabaseManager()
    
    if args.wipe:
        confirm = input("Are you sure you want to WIPE the database? (y/n): ")
        if confirm.lower() == 'y':
            db.wipe_database()
        else:
            print("Wipe cancelled.")
            
    if args.migrate:
        db.migrate_database()
        
    print(f"Database Manager initialized at {db.db_path}")
