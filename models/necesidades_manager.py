import json
from datetime import datetime
from models.models import db, Necesidad, DonacionFisica, DonacionMonetaria, Fundacion, Usuario

class NecesidadesManager:

    @staticmethod
    def crear_necesidad(fundacion_id, titulo, descripcion, cantidad_requerida, categoria, detalles_dict):
        try:
            nueva = Necesidad(
                fundacion_id=fundacion_id,
                titulo=titulo,
                descripcion=descripcion,
                cantidad_requerida=cantidad_requerida,
                categoria=categoria,
                detalles_json=json.dumps(detalles_dict),
                estado='activa'
            )
            db.session.add(nueva)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creando necesidad: {e}")
            return False

    @staticmethod
    def registrar_donacion_fisica(necesidad_id, donante_id, fundacion_id, articulo, cantidad, detalles_donacion):
        try:
            necesidad = Necesidad.query.filter_by(id=necesidad_id, estado='activa').with_for_update().first()
            if not necesidad:
                return False, "La necesidad no existe o ya no está disponible."

            nueva = DonacionFisica(
                necesidad_id=necesidad_id,
                donante_id=donante_id,
                fundacion_id=fundacion_id,
                articulo=articulo,
                cantidad_comprometida=cantidad,
                detalles_json=json.dumps(detalles_donacion)
            )
            db.session.add(nueva)
            
            # Actualizar necesidad
            necesidad.estado = 'finalizada'
            necesidad.cantidad_comprometida += cantidad
            
            db.session.commit()
            return True, "¡Donación registrada con éxito!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error crítico: {str(e)}"

    @staticmethod
    def obtener_donaciones_por_fundacion(fundacion_id):
        # Retorna lista de objetos DonacionFisica filtrada por fundacion
        return DonacionFisica.query.filter_by(fundacion_id=fundacion_id).order_by(DonacionFisica.created_at.desc()).all()

    @staticmethod
    def obtener_necesidades_activas():
        # Retorna necesidades activas
        return Necesidad.query.filter_by(estado='activa').order_by(Necesidad.created_at.desc()).all()

    @staticmethod
    def registrar_donacion_monetaria(necesidad_id, donante_id, monto, stripe_data):
        try:
            # 1. Registrar el pago
            nueva = DonacionMonetaria(
                necesidad_id=necesidad_id,
                usuario_id=donante_id,
                monto=monto,
                stripe_charge_id=stripe_data.get('charge_id'),
                card_brand=stripe_data.get('brand'),
                card_last4=stripe_data.get('last4'),
                email_donante=stripe_data.get('email')
            )
            db.session.add(nueva)

            # 2. Actualizar meta de necesidad
            necesidad = Necesidad.query.get(necesidad_id)
            if necesidad:
                necesidad.cantidad_comprometida += monto
                if necesidad.cantidad_comprometida >= necesidad.cantidad_requerida:
                    necesidad.estado = 'finalizada'
            
            db.session.commit()
            return True, "Pago registrado con éxito"
        except Exception as e:
            db.session.rollback()
            return False, str(e)