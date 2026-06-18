import bcrypt
from models.models import db, Usuario, Fundacion

class AuthManager:
    @staticmethod
    def verificar_login(email, password):
        try:
            # SQLAlchemy para buscar al usuario
            user = Usuario.query.filter_by(email=email).first()
            if not user:
                return None
            
            # Verificación de contraseña segura
            # Nos aseguramos de que los hashes sean comparables (tipo string/bytes)
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Validación de estado para fundaciones
                if user.rol == 'fundacion' and user.estado_validacion != 'aprobado':
                    print(f"Login bloqueado: {email} no aprobado.")
                    return None
                return user
            
            return None
        except Exception as e:
            print(f"Error crítico en login: {e}")
            return None
            
    @staticmethod
    def registrar_usuario(nombre, email, password, direccion, telefono, tipo, datos_fundacion=None):
        try:
            if Usuario.query.filter_by(email=email).first():
                return False

            # Generar hash de contraseña
            hash_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            nuevo_usuario = Usuario(
                nombre=nombre, 
                email=email, 
                password_hash=hash_pass,
                direccion=direccion or 'No especificada',
                telefono=telefono or '0000000000',
                rol='fundacion' if tipo == 'juridica' else 'donante',
                estado_validacion='pendiente'
            )
            db.session.add(nuevo_usuario)
            db.session.flush() # Importante para obtener nuevo_usuario.id antes del commit

            if tipo == 'juridica' and datos_fundacion:
                nueva_fundacion = Fundacion(
                    usuario_id=nuevo_usuario.id,
                    nit=datos_fundacion.get('nit'),
                    nombre_fundacion=datos_fundacion.get('nombre_fundacion'),
                    nombre_persona_cargo=nombre, 
                    descripcion=datos_fundacion.get('descripcion', 'Sin descripción'),
                    telefono=datos_fundacion.get('telefono'), # Agrega esto
                    email=datos_fundacion.get('email'), # Agrega esto
                    es_verificado=False
                )
                db.session.add(nueva_fundacion)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error en registro: {e}")
            return False