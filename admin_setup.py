from app import app
from database import get_db_connection

def convertir_a_admin(email):
    conn = get_db_connection()
    cur = conn.cursor()
    # Asumimos que tienes una columna 'rol' en tu tabla usuarios
    cur.execute("UPDATE usuarios SET rol = 'admin' WHERE email = %s", (email,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Usuario {email} ahora es Administrador.")

if __name__ == "__main__":
    convertir_a_admin("tu_correo@admin.com")