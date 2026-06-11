# database.py
import psycopg2
import os
from psycopg2.extras import RealDictCursor # IMPORTA ESTO

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    # Añadimos cursor_factory=RealDictCursor para que los resultados sean diccionarios
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor) 
    return conn
