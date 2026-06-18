import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """
    Establece una conexión con la base de datos PostgreSQL en Render.
    Usa RealDictCursor para obtener resultados como diccionarios.
    """
    try:
        # Render inyecta la variable DATABASE_URL automáticamente
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise Exception("La variable de entorno DATABASE_URL no está configurada.")
            
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Error crítico al conectar a la base de datos: {e}")
        # Re-lanzamos la excepción para que el modelo sepa que no hay conexión
        raise e