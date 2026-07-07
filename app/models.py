# app/models.py

CREATE_JOB_OFFERS_TABLE = """
CREATE TABLE IF NOT EXISTS job_offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,
    company TEXT NOT NULL,

    technical_requirements TEXT NOT NULL,
    minimum_experience_years INTEGER NOT NULL DEFAULT 0,
    desired_skills TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


CREATE_CANDIDATES_TABLE = """
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,
    email TEXT NOT NULL,

    cv_text TEXT NOT NULL,

    final_compatibility REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


CREATE_TABLES = [
    CREATE_JOB_OFFERS_TABLE,
    CREATE_CANDIDATES_TABLE
]