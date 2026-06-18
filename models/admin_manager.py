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
        return Usuario.query.filter_by(rol='donante').all()

    @staticmethod
    def obtener_listado_fundaciones():
        return Fundacion.query.order_by(Fundacion.created_at.desc()).all()

    @staticmethod
    def obtener_fundaciones_pendientes():
        return (
            Fundacion.query
            .filter_by(estado='pendiente')
            .order_by(Fundacion.created_at.desc())
            .all()
        )

    @staticmethod
    def obtener_listado_donaciones_completas():
        fisicas = (
            db.session.query(
                DonacionFisica.id.label('id'),
                Usuario.nombre.label('donante_nombre'),
                Fundacion.nombre_fundacion.label('fundacion_nombre'),
                DonacionFisica.articulo.label('necesidad_titulo'),
                DonacionFisica.cantidad_comprometida.label('cantidad_necesidad')
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
                DonacionMonetaria.monto.label('cantidad_necesidad')
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
                DonacionMonetaria.created_at.label('fecha_creacion')
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

        EmailService.enviar_notificacion(
            email_destino=fundacion.usuario.email,
            nombre_destino=fundacion.nombre_fundacion,
            asunto=asunto_por_estado.get(nuevo_estado, 'Actualizacion de fundacion'),
            mensaje=mensaje
        )
