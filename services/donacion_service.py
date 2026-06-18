import json
from decimal import Decimal

from models.models import db, DonacionFisica, DonacionMonetaria, Fundacion, Usuario, Necesidad


class DonacionService:
    """
    Capa de negocio para donaciones.
    Los controladores no deben consultar SQLAlchemy directamente.
    """

    # =========================
    # USUARIO
    # =========================
    @staticmethod
    def obtener_donante_por_id(usuario_id):
        try:
            user = Usuario.query.filter_by(id=usuario_id).first()
        except Exception as e:
            print(f"Error obteniendo donante: {e}")
            return None

        if not user:
            return None

        return {
            "id": user.id,
            "nombre": user.nombre,
            "email": user.email,
            "foto_perfil": "default.png"
        }

    @staticmethod
    def obtener_fundacion_id_por_usuario(usuario_id):
        try:
            fundacion = Fundacion.query.filter_by(usuario_id=usuario_id).first()
            return fundacion.id if fundacion else None
        except Exception as e:
            print(f"Error obteniendo fundacion por usuario: {e}")
            return None

    # =========================
    # NECESIDADES
    # =========================
    @staticmethod
    def obtener_necesidades_activas():
        try:
            return (
                Necesidad.query
                .filter_by(estado="activa")
                .order_by(Necesidad.created_at.desc())
                .all()
            )
        except Exception as e:
            print(f"Error obteniendo necesidades activas: {e}")
            return []

    # =========================
    # DONACIONES (LECTURA)
    # =========================
    @staticmethod
    def obtener_donaciones_usuario(usuario_id):
        try:
            fisicas = DonacionFisica.query.filter_by(donante_id=usuario_id).all()
            monetarias = DonacionMonetaria.query.filter_by(usuario_id=usuario_id).all()

            donaciones = []

            for donacion in fisicas:
                donaciones.append({
                    "tipo": "Fisica",
                    "articulo": donacion.articulo or "Donacion fisica",
                    "fecha": donacion.created_at,
                    "cantidad": donacion.cantidad_comprometida,
                    "estado": donacion.estado
                })

            for donacion in monetarias:
                donaciones.append({
                    "tipo": "Monetaria",
                    "articulo": "Donacion monetaria",
                    "fecha": donacion.created_at,
                    "cantidad": float(donacion.monto or 0),
                    "estado": "pagada"
                })

            return sorted(donaciones, key=lambda d: d["fecha"], reverse=True)
        except Exception as e:
            print(f"Error obteniendo donaciones del usuario: {e}")
            return []

    @staticmethod
    def obtener_donaciones_por_fundacion(fundacion_id):
        try:
            return (
                DonacionFisica.query
                .filter_by(fundacion_id=fundacion_id)
                .order_by(DonacionFisica.created_at.desc())
                .all()
            )
        except Exception as e:
            print(f"Error obteniendo donaciones por fundacion: {e}")
            return []

    @staticmethod
    def contar_donaciones_pendientes(fundacion_id):
        try:
            return DonacionFisica.query.filter_by(
                fundacion_id=fundacion_id,
                estado="pendiente"
            ).count()
        except Exception as e:
            print(f"Error contando donaciones pendientes: {e}")
            return 0

    # =========================
    # DONACIONES (ESCRITURA)
    # =========================
    @staticmethod
    def registrar_donacion_fisica(
        necesidad_id,
        donante_id,
        cantidad,
        detalles=None,
        fundacion_id=None,
        articulo=None
    ):
        try:
            necesidad = (
                Necesidad.query
                .filter_by(id=necesidad_id, estado="activa")
                .with_for_update()
                .first()
            )

            if not necesidad:
                return False, "La necesidad no existe o ya no esta disponible."

            cantidad = int(cantidad or 0)
            if cantidad <= 0:
                return False, "La cantidad debe ser mayor a cero."

            nueva = DonacionFisica(
                necesidad_id=necesidad.id,
                donante_id=donante_id,
                fundacion_id=fundacion_id or necesidad.fundacion_id,
                articulo=articulo or necesidad.titulo,
                cantidad_comprometida=cantidad,
                detalles_json=json.dumps(detalles or {}),
                estado="pendiente"
            )

            necesidad.cantidad_comprometida = (necesidad.cantidad_comprometida or 0) + cantidad
            if necesidad.cantidad_comprometida >= necesidad.cantidad_requerida:
                necesidad.estado = "finalizada"

            db.session.add(nueva)
            db.session.commit()
            return True, "Donacion fisica registrada correctamente"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def registrar_donacion_monetaria(usuario_id, necesidad_id, monto, stripe_data):
        try:
            necesidad = (
                Necesidad.query
                .filter_by(id=necesidad_id)
                .with_for_update()
                .first()
            )

            if not necesidad:
                return False, "La necesidad no existe."

            monto_decimal = Decimal(str(monto or 0))
            if monto_decimal <= 0:
                return False, "El monto debe ser mayor a cero."

            nueva = DonacionMonetaria(
                usuario_id=usuario_id,
                necesidad_id=necesidad.id,
                monto=monto_decimal,
                stripe_charge_id=stripe_data.get("charge_id"),
                card_brand=stripe_data.get("brand"),
                card_last4=stripe_data.get("last4"),
                email_donante=stripe_data.get("email")
            )

            necesidad.cantidad_comprometida = (necesidad.cantidad_comprometida or 0) + int(monto_decimal)
            if necesidad.cantidad_comprometida >= necesidad.cantidad_requerida:
                necesidad.estado = "finalizada"

            db.session.add(nueva)
            db.session.commit()
            return True, "Donacion monetaria registrada correctamente"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    # =========================
    # ESTADOS
    # =========================
    @staticmethod
    def cambiar_estado(donacion_id, nuevo_estado):
        try:
            estados_validos = {"pendiente", "recibida", "rechazada", "cancelada"}
            if nuevo_estado not in estados_validos:
                return False

            donacion = DonacionFisica.query.get(donacion_id)
            if not donacion:
                return False

            donacion.estado = nuevo_estado
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error cambiando estado: {e}")
            return False
