"""
Database Module for Student Study Planner
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'study_planner.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(seed_sample_data=True):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT NOT NULL DEFAULT '#6366f1',
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT NOT NULL,
        due_time TEXT DEFAULT '23:59',
        duration_mins INTEGER DEFAULT 45,
        priority TEXT DEFAULT 'Medium',
        is_completed INTEGER DEFAULT 0,
        completed_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    if seed_sample_data:
        cursor.execute("SELECT COUNT(*) FROM subjects;")
        if cursor.fetchone()[0] == 0:
            seed_data(conn)

    conn.close()

def seed_data(conn):
    cursor = conn.cursor()
    today_str = "2026-10-25"
    yesterday_str = "2026-10-24"
    future_str = "2026-10-28"

    sample_subjects = [
        ("Mathematics", "#4f46e5", "Linear Algebra & Calculus"),
        ("Computer Science", "#10b981", "Data Structures, Trees & Graphs"),
        ("Physics", "#f59e0b", "Mechanics & Dynamics"),
        ("English Literature", "#ec4899", "Shakespearean Plays & Essays")
    ]

    cursor.executemany("INSERT INTO subjects (name, color, description) VALUES (?, ?, ?);", sample_subjects)
    conn.commit()

    cursor.execute("SELECT id, name FROM subjects;")
    subj_map = {row['name']: row['id'] for row in cursor.fetchall()}

    sample_tasks = [
        (subj_map["Mathematics"], "Complete Linear Algebra Assignment 3", "Vector spaces and matrix transformations", today_str, "23:59", 120, "High", 0, None),
        (subj_map["Computer Science"], "Data Structures Trees & Graphs revision", "Review traversal algorithms and BST operations", today_str, "23:59", 90, "Medium", 0, None),
        (subj_map["Physics"], "Physics Mechanics Practice Set", "Newtonian laws and rotational motion problems", future_str, "23:59", 180, "High", 1, datetime.now().isoformat()),
        (subj_map["English Literature"], "Essay Draft on Hamlet Act 3", "Analyze character motives and themes", yesterday_str, "23:59", 150, "Low", 0, None)
    ]

    cursor.executemany("""
    INSERT INTO tasks (subject_id, title, description, due_date, due_time, duration_mins, priority, is_completed, completed_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, sample_tasks)

    conn.commit()