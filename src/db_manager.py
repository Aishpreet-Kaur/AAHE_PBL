import sqlite3
import pandas as pd
import os
from typing import List, Dict, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'hypotheses.db')

def init_db():
    """Initialize database with tables for hypotheses and sources"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Main hypotheses table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            theory TEXT NOT NULL,
            confidence REAL DEFAULT 0.5,
            credibility_explanation TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Sources/Citations table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hypothesis_id INTEGER NOT NULL,
            source_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            snippet TEXT,
            date_published TEXT,
            credibility_score REAL ,
            credibility_explanation TEXT,         
            source_type TEXT,
            date_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id) ON DELETE CASCADE
        );
        """)
        
        # Create index for faster lookups
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_hypothesis_sources 
        ON sources(hypothesis_id);
        """)
        cursor.execute("PRAGMA table_info(sources)")
        columns = [col[1] for col in cursor.fetchall()]

        if "credibility_explanation" not in columns:
            cursor.execute("ALTER TABLE sources ADD COLUMN credibility_explanation TEXT")
        
        conn.commit()


def save_theories_with_sources(topic: str, theory: str, sources: List[Dict]) -> int:
    """
    Save hypothesis and its associated sources.
    
    Returns:
        hypothesis_id: ID of the saved hypothesis
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Insert hypothesis
        cursor.execute(
            'INSERT INTO hypotheses (topic, theory) VALUES (?, ?)',
            (topic, theory)
        )
        hypothesis_id = cursor.lastrowid
        
        # Insert sources
        for source in sources:
        #     cursor.execute("""
        #         INSERT INTO sources (
        #             hypothesis_id, source_number, title, url, snippet, 
        #             date_published, credibility_score, source_type
        #         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        #     """, (
        #         hypothesis_id,
        #         source.get('id', 0),
        #         source.get('title', 'Unknown'),
        #         source.get('url', ''),
        #         source.get('snippet', ''),
        #         source.get('date', 'N/A'),
        #         source.get('credibility_score', 6.0),
        #         source.get('source_name', 'Web')
        #     ))

        # When inserting sources
            cursor.execute('''
                INSERT INTO sources 
                (hypothesis_id, source_number, title, url, snippet, date_published, 
                credibility_score, credibility_explanation, date_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hypothesis_id,
                source.get('id'),
                source.get('title'),
                source.get('url'),
                source.get('snippet'),
                source.get('date'),
                source.get('credibility_score'),
                source.get('credibility_explanation', ''),  # NEW
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
        
        conn.commit()
        return hypothesis_id


def save_theories(topic, theories):
    """Backward compatibility - save theories without sources"""
    with sqlite3.connect(DB_PATH) as conn:
        for th in theories:
            conn.execute('INSERT INTO hypotheses (topic, theory) VALUES (?, ?)', (topic, th))
        conn.commit()


def load_theories() -> pd.DataFrame:
    """Load all hypotheses"""
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql('SELECT * FROM hypotheses ORDER BY created_at DESC', conn)
    return df


def get_sources_for_hypothesis(hypothesis_id: int) -> List[Dict]:
    """Retrieve all sources associated with a hypothesis"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                source_number, title, url, snippet, 
                date_published, credibility_score, source_type
            FROM sources
            WHERE hypothesis_id = ?
            ORDER BY source_number
        """, (hypothesis_id,))
        
        rows = cursor.fetchall()
        
        sources = []
        for row in rows:
            sources.append({
                'number': row[0],
                'title': row[1],
                'url': row[2],
                'snippet': row[3],
                'date': row[4],
                'credibility': row[5],
                'type': row[6]
            })
        
        return sources


def get_hypothesis_with_sources(hypothesis_id: int) -> Optional[Dict]:
    """Get a hypothesis and all its sources"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Get hypothesis
        cursor.execute("""
            SELECT id, topic, theory, confidence, last_updated, created_at
            FROM hypotheses
            WHERE id = ?
        """, (hypothesis_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        hypothesis = {
            'id': row[0],
            'topic': row[1],
            'theory': row[2],
            'confidence': row[3],
            'last_updated': row[4],
            'created_at': row[5],
            'sources': get_sources_for_hypothesis(hypothesis_id)
        }
        
        return hypothesis


def clear_history():
    """Clear all hypotheses and sources"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM sources;")
        conn.execute("DELETE FROM hypotheses;")
        conn.commit()


def get_last_fetch_time(hypothesis_id: int) -> Optional[str]:
    """Get the last update time for a hypothesis"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT last_updated FROM hypotheses WHERE id = ?
    """, (hypothesis_id,))

    row = cur.fetchone()
    conn.close()

    return row[0] if row else None


def update_confidence(hypothesis_id: int, new_confidence: float):
    """Update hypothesis confidence score"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE hypotheses
        SET confidence = ?, last_updated = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_confidence, hypothesis_id))

    conn.commit()
    conn.close()


def get_hypothesis_by_id(hypothesis_id: int) -> Optional[Dict]:
    """Get basic hypothesis info by ID"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, topic, confidence, last_updated
        FROM hypotheses
        WHERE id = ?
    """, (hypothesis_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "topic": row[1],
        "confidence": row[2],
        "last_updated": row[3]
    }


def get_statistics() -> Dict:
    """Get database statistics"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Total hypotheses
        cursor.execute("SELECT COUNT(*) FROM hypotheses")
        total_hypotheses = cursor.fetchone()[0]
        
        # Total sources
        cursor.execute("SELECT COUNT(*) FROM sources")
        total_sources = cursor.fetchone()[0]
        
        # Average credibility
        cursor.execute("SELECT AVG(credibility_score) FROM sources")
        avg_credibility = cursor.fetchone()[0] or 0.0
        
        # Most recent analysis
        cursor.execute("""
            SELECT topic, created_at 
            FROM hypotheses 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        recent = cursor.fetchone()
        
        return {
            'total_hypotheses': total_hypotheses,
            'total_sources': total_sources,
            'avg_credibility': round(avg_credibility, 2),
            'most_recent_topic': recent[0] if recent else 'None',
            'most_recent_date': recent[1] if recent else 'N/A'
        }