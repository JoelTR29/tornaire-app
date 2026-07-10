# app/models.py

# 1. Nova taula per gestionar les credencials de login i registre
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,           -- 'candidat' o 'empresa'
    nom TEXT NOT NULL,
    nom_empresa TEXT,             -- Només s'omplirà si el rol és 'empresa'
    email TEXT UNIQUE NOT NULL,   -- El 'UNIQUE' evita que es registrin dos cops el mateix correu
    password TEXT NOT NULL,       -- Contrasenya (en un MVP local la guardarem com a text)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# 2. Modificada per coincidir amb els camps del formulari HTML i lligar-la a una empresa
CREATE_JOB_OFFERS_TABLE = """
CREATE TABLE IF NOT EXISTS job_offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,     -- ID de l'empresa (user) que ha creat l'oferta
    title TEXT NOT NULL,          -- Títol del lloc
    location TEXT NOT NULL,       -- Ubicació
    modality TEXT NOT NULL,       -- Presencial / Híbrid / Remot
    salary TEXT NOT NULL,         -- Salari
    contact_email TEXT NOT NULL,  -- Correu de contacte
    description TEXT NOT NULL,    -- Descripció de la posició
    technical_requirements TEXT NOT NULL, -- Requisits per a la IA
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""

# 3. Modificada per desar el CV vinculat a l'ID del candidat que ha iniciat sessió
CREATE_CANDIDATES_TABLE = """
CREATE TABLE IF NOT EXISTS candidates_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,  -- Vinculat a l'usuari candidat
    cv_text TEXT NOT NULL,            -- Text extret del PDF o del formulari manual
    final_compatibility REAL,         -- Percentatge de matching
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""

CREATE_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_JOB_OFFERS_TABLE,
    CREATE_CANDIDATES_TABLE
]