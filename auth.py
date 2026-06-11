import bcrypt
from database import get_db_connection
import uuid
from datetime import datetime
from psycopg2.extras import RealDictCursor # Importamos esto para asegurar diccionarios

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
    def registrar_usuario(nombre, email, password, direccion, telefono, tipo):
        if "@" not in email: return False
        
        bytes_pass = password.encode('utf-8')
        hash_pass = bcrypt.hashpw(bytes_pass, bcrypt.gensalt()).decode('utf-8')
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO usuarios (nombre, email, password_hash, direccion, telefono, tipo_persona) VALUES (%s, %s, %s, %s, %s, %s)",
                (nombre, email, hash_pass, direccion, telefono, tipo)
            )
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def verificar_login(email, password):
        conn = get_db_connection()
        # FORZAMOS EL USO DE RealDictCursor AQUÍ para asegurar que devuelva un diccionario
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            user = cur.fetchone()
            
            if user:
                # Verificación de hash
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
        if "@" not in email: return False
        
        bytes_pass = password.encode('utf-8')
        hash_pass = bcrypt.hashpw(bytes_pass, bcrypt.gensalt()).decode('utf-8')
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. Insertar el Usuario y obtener su ID recién creado
            # Nota: Asegúrate que tu tabla usuarios tenga el campo 'rol'
            cur.execute(
                "INSERT INTO usuarios (nombre, email, password_hash, direccion, telefono, tipo_persona, rol) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (nombre, email, hash_pass, direccion, telefono, tipo, 'fundacion' if tipo == 'juridica' else 'donante')
            )
            usuario_id = cur.fetchone()[0]

            # 2. Si es jurídica, insertar en la tabla fundaciones
            if tipo == 'juridica' and datos_fundacion:
                cur.execute(
                    """INSERT INTO fundaciones (usuario_id, nit, nombre_fundacion, nombre_persona_cargo, descripcion) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (usuario_id, datos_fundacion['nit'], datos_fundacion['nombre_fundacion'], 
                     datos_fundacion['nombre_persona_cargo'], datos_fundacion['descripcion'])
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback() # Seguridad: si algo falla, no dejamos datos huérfanos
            print(f"Error en registro: {e}")
            return False
        finally:
            cur.close()
            conn.close()        
