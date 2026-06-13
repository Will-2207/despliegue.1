import bcrypt
from database import get_db_connection
import uuid
from psycopg2.extras import RealDictCursor

class SoporteManager:
    @staticmethod
    def procesar_soporte(datos):
        nombre = datos.get('nombre_contacto', '').strip()
        email = datos.get('email_contacto', '').strip()
        titulo = datos.get('titulo_falla', '').strip()
        token = uuid.uuid4().hex

        if not nombre or not email or not titulo:
            return {'tipo': 'error', 'mensaje': 'Datos obligatorios incompletos.'}

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            sql = """INSERT INTO tickets_soporte 
                     (nombre, email, telefono, rol, categoria, prioridad, titulo, descripcion, pasos, token) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cur.execute(sql, (
                nombre, email, datos.get('telefono_contacto'), datos.get('rol_usuario'),
                datos.get('categoria_fallo'), datos.get('prioridad'), titulo,
                datos.get('descripcion_falla'), datos.get('pasos_reproduccion'), token
            ))
            conn.commit()
            cur.close()
            conn.close()
            return {'tipo': 'success', 'mensaje': 'Ticket creado correctamente.', 'token': token}
        except Exception as e:
            return {'tipo': 'error', 'mensaje': f'Error al guardar el ticket: {str(e)}'}

class AuthManager:
    @staticmethod
    def verificar_login(email, password):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            user = cur.fetchone()
            
            if user:
                # BYPASS TOTAL: Si el usuario es el admin, entramos sí o sí.
                if email == 'admin@redsolidaria.com' and password == 'admin123':
                    return user
                # Si no es el admin, usamos bcrypt normal
                if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    return user
            return None
        except Exception as e:
            print(f"Error en login: {e}")
            return None
        finally:
            cur.close()
            conn.close()
            
    @staticmethod
    def registrar_usuario(nombre, email, password, direccion, telefono, tipo, datos_fundacion=None):
        if not nombre or not email or not password: 
            return False
            
        bytes_pass = password.encode('utf-8')
        hash_pass = bcrypt.hashpw(bytes_pass, bcrypt.gensalt()).decode('utf-8')
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. Intentamos el INSERT
            sql = """INSERT INTO usuarios (nombre, email, password_hash, direccion, telefono, tipo_persona, rol) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id"""
            valores = (nombre, email, hash_pass, direccion or 'N/A', telefono or '000', tipo or 'natural', 'fundacion' if tipo == 'juridica' else 'donante')
            
            cur.execute(sql, valores)
            res = cur.fetchone()
            
            if not res:
                # Esto nos dirá si el insert fue ignorado
                print("DEBUG CRITICO: El insert fue exitoso pero no retornó ID.")
                return False
                
            usuario_id = res[0]

            # 2. Inserción de fundación
            if tipo == 'juridica' and datos_fundacion:
                cur.execute(
                    """INSERT INTO fundaciones (usuario_id, nit, nombre_fundacion, nombre_persona_cargo, descripcion) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (usuario_id, datos_fundacion.get('nit'), datos_fundacion.get('nombre_fundacion'), 
                     nombre, datos_fundacion.get('descripcion', 'Sin descripción'))
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            # Capturamos el error real de la base de datos
            import traceback
            error_msg = traceback.format_exc()
            print(f"--- ERROR DE BASE DE DATOS ---\n{error_msg}")
            return False
        finally:
            cur.close()
            conn.close()