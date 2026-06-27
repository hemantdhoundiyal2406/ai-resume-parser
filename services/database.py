import json
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database.db"


def get_connection():
    """Create a SQLite connection and return rows like dictionaries."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the database table the first time the app runs."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                name TEXT,
                email TEXT,
                phone TEXT,
                skills TEXT,
                education TEXT,
                experience TEXT,
                projects TEXT,
                summary TEXT,
                job_description TEXT,
                matching_skills TEXT,
                missing_skills TEXT,
                job_fit_score INTEGER,
                resume_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def to_json(value):
    """Store Python lists in SQLite as JSON text."""
    return json.dumps(value or [])


def from_json(value):
    """Convert JSON text from SQLite back into a Python list."""
    if not value:
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return []


def save_resume(data):
    """Save one parsed resume and return its new database id."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO resumes (
                filename, name, email, phone, skills, education, experience,
                projects, summary, job_description, matching_skills,
                missing_skills, job_fit_score, resume_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("filename", ""),
                data.get("name", ""),
                data.get("email", ""),
                data.get("phone", ""),
                to_json(data.get("skills")),
                to_json(data.get("education")),
                to_json(data.get("experience")),
                to_json(data.get("projects")),
                data.get("summary", ""),
                data.get("job_description", ""),
                to_json(data.get("matching_skills")),
                to_json(data.get("missing_skills")),
                data.get("job_fit_score"),
                data.get("resume_text", ""),
            ),
        )
        connection.commit()
        return cursor.lastrowid


def row_to_resume(row):
    """Prepare one database row for templates or JSON download."""
    if row is None:
        return None

    resume = dict(row)
    for key in ["skills", "education", "experience", "projects", "matching_skills", "missing_skills"]:
        resume[key] = from_json(resume.get(key))
    return resume


def get_all_resumes():
    """Return all parsed resumes, newest first."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, filename, name, email, phone, skills, job_fit_score, created_at
            FROM resumes
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [row_to_resume(row) for row in rows]


def get_resume_by_id(resume_id):
    """Return one parsed resume by id."""
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
        return row_to_resume(row)
