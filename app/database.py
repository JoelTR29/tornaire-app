# app/database.py

import sqlite3
from pathlib import Path

from app.models import CREATE_TABLES


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "tornaire.db"


def get_connection():
    """
    Abre una conexión con la base de datos SQLite.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """
    Crea la base de datos y las tablas si no existen.
    """
    connection = get_connection()

    try:
        cursor = connection.cursor()

        for table in CREATE_TABLES:
            cursor.execute(table)

        connection.commit()

    finally:
        connection.close()