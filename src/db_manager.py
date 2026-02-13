import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hypotheses.db')

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS hypotheses;")
        conn.execute("""
        CREATE TABLE hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            theory TEXT,
            confidence REAL DEFAULT 0.5,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()



def save_theories(topic, theories):
    with sqlite3.connect(DB_PATH) as conn:
        for th in theories:
            conn.execute('INSERT INTO hypotheses (topic, theory) VALUES (?, ?)', (topic, th))
        conn.commit()

def load_theories():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql('SELECT * FROM hypotheses', conn)
    return df

def clear_history():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM hypotheses;")
        conn.commit()

def get_last_fetch_time(hypothesis_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT last_updated FROM hypotheses WHERE id = ?
    """, (hypothesis_id,))

    row = cur.fetchone()
    conn.close()

    return row[0] if row else None


def update_confidence(hypothesis_id, new_confidence):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE hypotheses
        SET confidence = ?, last_updated = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_confidence, hypothesis_id))

    conn.commit()
    conn.close()

def get_hypothesis_by_id(hypothesis_id: int):
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