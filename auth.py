import bcrypt
import uuid
from database import get_db_connection
from models import db, Usuario, Fundacion # Importamos SQLAlchemy y los modelos

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
            # Soporte se mantiene con psycopg2 porque no tenemos modelo en models.py aún
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
        try:
            # Usamos SQLAlchemy para buscar al usuario
            user = Usuario.query.filter_by(email=email).first()
            
            if user:
                # 1. BYPASS TOTAL: Si es el admin, entra directo
                if email == 'admin@redsolidaria.com' and password == 'admin123':
                    return user
                
                # 2. SEGURIDAD: Si es fundación, debe estar aprobado
                if user.rol == 'fundacion' and user.estado_validacion != 'aprobado':
                    print(f"Intento de login bloqueado: {email} no está aprobado.")
                    return None # Retornamos None para que el controlador muestre error
                
                # 3. Verificación de contraseña con bcrypt
                if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                    return user
            
            return None
        except Exception as e:
            print(f"Error crítico en login: {e}")
            return None
            
    @staticmethod
    def registrar_usuario(nombre, email, password, direccion, telefono, tipo, datos_fundacion=None):
        if not nombre or not email or not password: 
            print("DEBUG: Faltan datos obligatorios (nombre, email o pass)")
            return False
            
        try:
            # Verificamos si el correo ya está registrado antes de hacer nada
            if Usuario.query.filter_by(email=email).first():
                print("DEBUG: El email ya existe en la base de datos.")
                return False

            bytes_pass = password.encode('utf-8')
            hash_pass = bcrypt.hashpw(bytes_pass, bcrypt.gensalt()).decode('utf-8')
            
            # 1. Creamos el usuario en SQLAlchemy
            nuevo_usuario = Usuario(
                nombre=nombre,
                email=email,
                password_hash=hash_pass,
                direccion=direccion or 'No especificada',
                telefono=telefono or '0000000000',
                rol='fundacion' if tipo == 'juridica' else 'donante',
                estado_validacion='pendiente'
            )
            
            # Agregamos y hacemos flush para obtener el ID sin cerrar la transacción
            db.session.add(nuevo_usuario)
            db.session.flush() 

            # 2. Si es fundación, la relacionamos con el usuario recién creado
            if tipo == 'juridica' and datos_fundacion:
                nueva_fundacion = Fundacion(
                    usuario_id=nuevo_usuario.id,
                    nit=datos_fundacion.get('nit'),
                    nombre_fundacion=datos_fundacion.get('nombre_fundacion'),
                    nombre_persona_cargo=nombre, 
                    descripcion=datos_fundacion.get('descripcion', 'Sin descripción'),
                    es_verificado=False
                )
                db.session.add(nueva_fundacion)
            
            # 3. Confirmamos ambos registros en la base de datos al mismo tiempo
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback() # Si algo falla, deshacemos todo para no dejar datos a medias
            import traceback
            print(f"--- ERROR CRÍTICO DE REGISTRO ---")
            print(traceback.format_exc())
            return False