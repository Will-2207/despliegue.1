import os
import uuid

from werkzeug.security import check_password_hash, generate_password_hash

from models.models import db, Usuario, Fundacion


class AuthService:
    @staticmethod
    def autenticar_usuario(email, password):
        try:
            usuario = Usuario.query.filter_by(email=email).first()

            if not usuario or not check_password_hash(usuario.password_hash, password):
                return False, "Correo o contrasena incorrectos.", None

            if usuario.rol == "fundacion":
                fundacion = Fundacion.query.filter_by(usuario_id=usuario.id).first()

                if not fundacion:
                    return False, "La cuenta de fundacion no esta configurada correctamente.", None

                if fundacion.estado == "pendiente":
                    return False, "Tu fundacion aun esta pendiente de aprobacion.", None

                if fundacion.estado == "rechazada":
                    return False, "Tu solicitud de fundacion fue rechazada.", None

                if fundacion.estado == "suspendida":
                    return False, "Tu fundacion se encuentra suspendida.", None

                if fundacion.estado != "activa":
                    return False, "Tu fundacion no esta habilitada para ingresar.", None

            return True, "Autenticacion exitosa.", usuario
        except Exception as e:
            print(f"Error autenticando usuario: {e}")
            return False, "Error inesperado al iniciar sesion.", None

    @staticmethod
    def fundacion_activa(usuario_id):
        try:
            fundacion = Fundacion.query.filter_by(usuario_id=usuario_id).first()
            return bool(fundacion and fundacion.estado == "activa")
        except Exception as e:
            print(f"Error validando estado de fundacion: {e}")
            return False

    @staticmethod
    def registrar_usuario(form):
        try:
            nombre = form.get("nombre")
            email = form.get("email")
            password = form.get("pass")
            direccion = form.get("direccion")
            telefono = form.get("telefono")
            tipo_persona = form.get("tipo_persona")

            if not nombre or not email or not password or not direccion or not telefono or not tipo_persona:
                return False, "Por favor, completa todos los campos obligatorios."

            if Usuario.query.filter_by(email=email).first():
                return False, "El correo ya esta registrado."

            es_fundacion = tipo_persona == "juridica"
            if es_fundacion:
                campos_fundacion = [
                    form.get("nombre_fundacion"),
                    form.get("nit"),
                    form.get("nombre_persona_cargo"),
                    form.get("descripcion")
                ]
                if not all(campos_fundacion):
                    return False, "Completa todos los datos de la fundacion."

            nuevo_usuario = Usuario(
                nombre=nombre,
                email=email,
                direccion=direccion,
                password_hash=generate_password_hash(password),
                rol="fundacion" if es_fundacion else "donante"
            )
            db.session.add(nuevo_usuario)
            db.session.flush()

            if es_fundacion:
                nueva_fundacion = Fundacion(
                    usuario_id=nuevo_usuario.id,
                    nombre_fundacion=form.get("nombre_fundacion"),
                    nit=form.get("nit"),
                    nombre_persona_cargo=form.get("nombre_persona_cargo"),
                    telefono=telefono,
                    descripcion=form.get("descripcion"),
                    estado="pendiente"
                )
                db.session.add(nueva_fundacion)

            db.session.commit()

            if es_fundacion:
                return True, "Registro recibido. Tu fundacion queda pendiente de aprobacion."

            return True, "Registro exitoso, por favor inicia sesion."
        except Exception as e:
            db.session.rollback()
            print(f"Error registrando usuario: {e}")
            return False, "Error inesperado al registrar la cuenta."
        
        

    @staticmethod
    def actualizar_perfil_usuario(usuario_id, form, files, app_root_path, rol_usuario="donante"):
        try:
            usuario = Usuario.query.get(usuario_id)
            if not usuario:
                return False, "No fue posible encontrar el usuario.", None

            # 1. Procesamiento común del Archivo de Imagen (UUID estricto)
            filename_db = None
            file = files.get("foto_perfil")
            if file and file.filename:
                extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
                if extension not in {"jpg", "jpeg", "png", "webp"}:
                    return False, "Formato de imagen no permitido.", None

                filename = f"{uuid.uuid4().hex}.{extension}"
                upload_folder = os.path.join(app_root_path, "static", "uploads")
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                # Guardamos la referencia relativa estándar
                filename_db = f"uploads/{filename}"

            # 2. Lógica separada por Roles
            if rol_usuario == "fundacion":
                fundacion = Fundacion.query.filter_by(usuario_id=usuario_id).first()
                if not fundacion:
                    return False, "No fue posible encontrar la fundación.", None

                nombre_fundacion = form.get("nombre_fundacion")
                telefono = form.get("telefono")
                email = form.get("email")

                if not nombre_fundacion or not telefono or not email:
                    return False, "El nombre, teléfono y email son obligatorios.", None

                fundacion.nombre_fundacion = nombre_fundacion
                fundacion.nombre_persona_cargo = form.get("nombre_encargado")
                fundacion.telefono = telefono
                usuario.email = email
                
                # Para fundaciones viejas que usan la columna en la tabla fundacion
                if filename_db:
                    fundacion.foto_perfil = filename_db
                    usuario.foto_perfil = filename_db # Espejo en tabla usuarios

                nombre_retorno = fundacion.nombre_fundacion

            else:
                # ── LÓGICA EXCLUSIVA PARA EL DONANTE CORREGIDA ──
                nombre_donante = form.get("nombre")
                email = form.get("email")
                # Capturamos el teléfono del formulario para el donante
                telefono_donante = form.get("telefono")

                if not nombre_donante or not email:
                    return False, "El nombre y el email son campos obligatorios.", None

                usuario.nombre = nombre_donante
                usuario.email = email
                usuario.telefono = telefono_donante # Ahora sí se guardará de forma infalible en PostgreSQL
                
                if filename_db:
                    usuario.foto_perfil = filename_db

                nombre_retorno = usuario.nombre

            db.session.commit()
            db.session.expire_all()

            return True, "Perfil actualizado correctamente.", nombre_retorno
        except Exception as e:
            db.session.rollback()
            print(f"Error actualizando perfil multi-rol: {e}")
            return False, "Error inesperado al actualizar el perfil.", None