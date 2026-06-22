from models.models import db, DonacionFisica, DonacionMonetaria, Usuario, Necesidad

class DonacionModel:
    """
    Clase centralizada usando SQLAlchemy. 
    Nota: Todos los métodos de DB ahora usan SQLAlchemy directamente.
    """

    @staticmethod
    def obtener_donaciones_por_usuario(usuario_id):
        """Obtiene una lista unificada de ambas donaciones."""
        fisicas = DonacionFisica.query.filter_by(donante_id=usuario_id).all()
        monetarias = DonacionMonetaria.query.filter_by(usuario_id=usuario_id).all()
        return fisicas + monetarias

    @staticmethod
    def registrar_donacion_fisica(donante_id, fundacion_id, articulo, cantidad, detalles):
        try:
            nueva = DonacionFisica(
                donante_id=donante_id,
                fundacion_id=fundacion_id,
                articulo=articulo,
                cantidad_comprometida=cantidad,
                detalles_json=detalles,
                estado='pendiente'
            )
            db.session.add(nueva)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error registrando donación física: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def registrar_donacion_monetaria(usuario_id, necesidad_id, monto, stripe_id, brand, last4, email):
        try:
            # 1. Traemos la necesidad afectada para sumarle el recaudo de una vez
            necesidad = Necesidad.query.get(necesidad_id)
            
            nueva = DonacionMonetaria(
                usuario_id=usuario_id,
                necesidad_id=necesidad_id,
                monto=monto,
                stripe_charge_id=stripe_id,
                card_brand=brand,
                card_last4=last4,
                email_donante=email
            )
            db.session.add(nueva)

            # 2. Si la necesidad existe, le sumamos el monto recaudado
            if necesidad:
                necesidad.cantidad_comprometida = (necesidad.cantidad_comprometida or 0) + int(float(monto))
                # Si llegó a la meta, la marcamos como finalizada
                if necesidad.cantidad_comprometida >= necesidad.cantidad_requerida:
                    necesidad.estado = 'finalizada'

            db.session.commit()
            return True
        except Exception as e:
            print(f"Error registrando donación monetaria: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def contar_donaciones_pendientes(fundacion_id):
        """Cuenta donaciones físicas pendientes para el dashboard de la fundación."""
        return DonacionFisica.query.filter_by(
            fundacion_id=fundacion_id, 
            estado='pendiente'
        ).count()

    @staticmethod
    def obtener_detalle_donacion_fisica(donacion_id):
        return DonacionFisica.query.get(donacion_id)

    @staticmethod
    def actualizar_estado_donacion(donacion_id, nuevo_estado):
        try:
            donacion = DonacionFisica.query.get(donacion_id)
            if donacion:
                donacion.estado = nuevo_estado
                db.session.commit()
                return True
        except Exception as e:
            print(f"Error actualizando estado: {e}")
            db.session.rollback()
        return False