from models.models import db, Usuario, Fundacion, Necesidad, DonacionFisica, DonacionMonetaria
from email_service import EmailService


class AdminManager:
    @staticmethod
    def obtener_metricas():
        donaciones_fisicas_count = DonacionFisica.query.count()
        donaciones_monetarias_count = DonacionMonetaria.query.count()

        return {
            'donantes': Usuario.query.filter_by(rol='donante').count(),
            'fundaciones': Fundacion.query.count(),
            'donaciones': donaciones_fisicas_count + donaciones_monetarias_count,
            'pagos': donaciones_monetarias_count,
            'pendientes': Fundacion.query.filter_by(estado='pendiente').count()
        }

    @staticmethod
    def obtener_listado_donantes():
        # ── CORREGIDO: el HTML espera d.correo, d.fecha_registro, d.estado
        # -- nombres que NO existen tal cual en el modelo Usuario real
        # (son email, created_at; 'estado' no existe en absoluto, solo
        # 'rol'). Se devuelven diccionarios con los nombres correctos
        # sin tocar el modelo ni la base de datos. ──
        donantes = Usuario.query.filter_by(rol='donante').all()
        return [
            {
                'id': u.id,
                'nombre': u.nombre,
                'correo': u.email,
                'fecha_registro': u.created_at.strftime('%d/%m/%Y') if u.created_at else '—',
                'estado': 'aprobado'  # Usuario no tiene estado propio; todo donante activo se considera aprobado
            }
            for u in donantes
        ]

    @staticmethod
    def obtener_listado_fundaciones():
        # ── CORREGIDO: el HTML espera f.nombre, f.correo, f.fecha_registro,
        # f.estado_validacion -- nombres que NO existen tal cual en el
        # modelo Fundacion real (es nombre_fundacion, created_at, estado;
        # el correo vive en Usuario.email vía la relación fundacion.usuario). ──
        fundaciones = Fundacion.query.order_by(Fundacion.created_at.desc()).all()
        return [
            {
                'id': f.id,
                'nombre': f.nombre_fundacion,
                'nit': f.nit,
                'correo': f.usuario.email if f.usuario else '—',
                'fecha_registro': f.created_at.strftime('%d/%m/%Y') if f.created_at else '—',
                'estado_validacion': f.estado
            }
            for f in fundaciones
        ]

    @staticmethod
    def obtener_fundaciones_pendientes():
        fundaciones = (
            Fundacion.query
            .filter_by(estado='pendiente')
            .order_by(Fundacion.created_at.desc())
            .all()
        )
        return [
            {
                'id': f.id,
                'nombre': f.nombre_fundacion,
                'nit': f.nit,
                'correo': f.usuario.email if f.usuario else '—',
                'fecha_registro': f.created_at.strftime('%d/%m/%Y') if f.created_at else '—',
                'estado_validacion': f.estado
            }
            for f in fundaciones
        ]

    @staticmethod
    def obtener_listado_donaciones_completas():
        # ── AMPLIADO: se agregan created_at y estado a ambas queries,
        # para que admin_dashboard.html pueda mostrar fecha y estado
        # reales en la tabla de "Historial de Donaciones Físicas".
        # No se modifica ninguna columna ya existente, solo se agregan
        # 2 nuevas al SELECT. ──
        fisicas = (
            db.session.query(
                DonacionFisica.id.label('id'),
                Usuario.nombre.label('donante_nombre'),
                Fundacion.nombre_fundacion.label('fundacion_nombre'),
                DonacionFisica.articulo.label('necesidad_titulo'),
                DonacionFisica.cantidad_comprometida.label('cantidad_necesidad'),
                DonacionFisica.created_at.label('fecha_creacion'),
                DonacionFisica.estado.label('estado_donacion')
            )
            .outerjoin(Usuario, DonacionFisica.donante_id == Usuario.id)
            .outerjoin(Fundacion, DonacionFisica.fundacion_id == Fundacion.id)
            .all()
        )

        monetarias = (
            db.session.query(
                DonacionMonetaria.id.label('id'),
                Usuario.nombre.label('donante_nombre'),
                Fundacion.nombre_fundacion.label('fundacion_nombre'),
                Necesidad.titulo.label('necesidad_titulo'),
                DonacionMonetaria.monto.label('cantidad_necesidad'),
                DonacionMonetaria.created_at.label('fecha_creacion'),
                DonacionMonetaria.estado.label('estado_donacion')
            )
            .outerjoin(Usuario, DonacionMonetaria.usuario_id == Usuario.id)
            .outerjoin(Necesidad, DonacionMonetaria.necesidad_id == Necesidad.id)
            .outerjoin(Fundacion, Necesidad.fundacion_id == Fundacion.id)
            .all()
        )

        return fisicas + monetarias

    @staticmethod
    def obtener_pagos():
        return (
            db.session.query(
                DonacionMonetaria.id.label('id'),
                Usuario.nombre.label('donante_nombre'),
                Fundacion.nombre_fundacion.label('fundacion_nombre'),
                DonacionMonetaria.monto.label('monto'),
                DonacionMonetaria.created_at.label('fecha_creacion'),
                DonacionMonetaria.estado.label('estado_pago')
            )
            .outerjoin(Usuario, DonacionMonetaria.usuario_id == Usuario.id)
            .outerjoin(Necesidad, DonacionMonetaria.necesidad_id == Necesidad.id)
            .outerjoin(Fundacion, Necesidad.fundacion_id == Fundacion.id)
            .order_by(DonacionMonetaria.created_at.desc())
            .all()
        )

    @staticmethod
    def validar_fundacion(fundacion_id, nuevo_estado, motivo=''):
        estados_validos = {'activa', 'rechazada', 'suspendida'}
        if nuevo_estado not in estados_validos:
            return False, "Estado de fundacion no permitido."

        try:
            fundacion = Fundacion.query.get(fundacion_id)
            if not fundacion:
                return False, "Fundacion no encontrada."

            fundacion.estado = nuevo_estado
            db.session.commit()

            AdminManager._notificar_cambio_estado(fundacion, nuevo_estado, motivo)
            return True, "Accion procesada correctamente."
        except Exception as e:
            db.session.rollback()
            print(f"Error validando fundacion: {e}")
            return False, "Error al procesar la accion."

    @staticmethod
    def dar_baja_donante(donante_id, motivo=''):
        """
        Da de baja a un donante usando la columna 'rol' ya existente en
        Usuario (sin agregar columnas nuevas ni requerir migración).
        El donante no se borra de la BD, queda marcado como inactivo
        para conservar el historial de sus donaciones pasadas.
        """
        try:
            donante = Usuario.query.get(donante_id)
            if not donante or donante.rol != 'donante':
                return False, "Donante no encontrado."

            donante.rol = 'donante_inactivo'
            db.session.commit()

            AdminManager._notificar_baja_donante(donante, motivo)
            return True, "Donante dado de baja correctamente."
        except Exception as e:
            db.session.rollback()
            print(f"Error dando de baja al donante: {e}")
            return False, "Error al procesar la accion."

    @staticmethod
    def _notificar_cambio_estado(fundacion, nuevo_estado, motivo):
        if not fundacion.usuario or not fundacion.usuario.email:
            return

        asunto_por_estado = {
            'activa': 'Tu fundacion fue aprobada',
            'rechazada': 'Resultado de revision de tu fundacion',
            'suspendida': 'Tu fundacion fue suspendida'
        }

        mensaje_por_estado = {
            'activa': 'Tu fundacion ya fue aprobada y puedes ingresar a Red Solidaria.',
            'rechazada': 'Tu solicitud fue revisada y no fue aprobada en este momento.',
            'suspendida': 'Tu fundacion fue suspendida por el equipo administrativo.'
        }

        mensaje = mensaje_por_estado.get(nuevo_estado, 'El estado de tu fundacion fue actualizado.')
        if motivo:
            mensaje = f"{mensaje}<br><br><strong>Motivo:</strong> {motivo}"

        html_content = f"<html><body><h3>Hola, {fundacion.nombre_fundacion}</h3><p>{mensaje}</p></body></html>"

        # ── FIX: EmailService.enviar_notificacion espera 'html_content',
        # no 'mensaje'. Antes este parametro no existia en la firma real
        # y la llamada fallaba en silencio (atrapada por el try/except de
        # validar_fundacion), por lo que el correo nunca se enviaba. ──
        EmailService.enviar_notificacion(
            email_destino=fundacion.usuario.email,
            nombre_destino=fundacion.nombre_fundacion,
            asunto=asunto_por_estado.get(nuevo_estado, 'Actualizacion de fundacion'),
            html_content=html_content
        )

    @staticmethod
    def _notificar_baja_donante(donante, motivo):
        if not donante.email:
            return

        mensaje = "Tu cuenta en Red Solidaria ha sido dada de baja por el equipo administrativo."
        if motivo:
            mensaje = f"{mensaje}<br><br><strong>Motivo:</strong> {motivo}"

        html_content = f"<html><body><h3>Hola, {donante.nombre}</h3><p>{mensaje}</p></body></html>"

        EmailService.enviar_notificacion(
            email_destino=donante.email,
            nombre_destino=donante.nombre,
            asunto="Tu cuenta fue dada de baja - Red Solidaria",
            html_content=html_content
        )