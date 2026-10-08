"""SQLite access; preserves the original submissions schema and database path."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

import pandas as pd


@contextmanager
def connection():
    con = sqlite3.connect(os.environ.get('HOMEWORK_DB_PATH', 'homework.db'), timeout=15)
    try:
        con.execute('''CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, submitted_at TEXT NOT NULL,
            student TEXT NOT NULL, day INTEGER NOT NULL, attempt INTEGER NOT NULL,
            score INTEGER NOT NULL, total INTEGER NOT NULL, accuracy REAL NOT NULL,
            elapsed_sec INTEGER NOT NULL, wrong_types TEXT NOT NULL)''')
        yield con
        con.commit()
    finally:
        con.close()


def save_submission(student, day, score, total, elapsed, wrong_types):
    accuracy = round(score / total * 100, 1)
    with connection() as con:
        # Serialize the attempt number and insertion across simultaneous submissions.
        con.execute('BEGIN IMMEDIATE')
        attempt = con.execute(
            'SELECT COALESCE(MAX(attempt),0)+1 FROM submissions WHERE student=? AND day=?',
            (student, day),
        ).fetchone()[0]
        con.execute(
            '''INSERT INTO submissions
            (submitted_at,student,day,attempt,score,total,accuracy,elapsed_sec,wrong_types)
            VALUES (?,?,?,?,?,?,?,?,?)''',
            (datetime.now().isoformat(timespec='seconds'), student, day, attempt,
             score, total, accuracy, elapsed, wrong_types),
        )
    return attempt, accuracy


def read_submissions(student=None):
    with connection() as con:
        if student is None:
            return pd.read_sql_query('SELECT * FROM submissions ORDER BY id DESC', con)
        return pd.read_sql_query(
            'SELECT * FROM submissions WHERE student=? ORDER BY id DESC', con, params=(student,)
        )
