from flask import session, request
from datetime import datetime
from models import db, Usuario, Fundacion, Necesidad, Donacion, Auditoria

class AdminManager:
    
    @staticmethod
    def registrar_auditoria(recurso_afectado, accion, motivo):
        admin_id = session.get('user_id')
        
        # Si no hay admin_id, salimos para evitar el error 500 y permitir que la acción se complete
        if admin_id is None:
            print("AVISO: No se pudo registrar auditoría, admin_id es None.")
            return

        try:
            log = Auditoria(
                admin_id=admin_id,
                recurso_afectado=recurso_afectado,
                accion=accion,
                motivo=motivo,
                ip=request.remote_addr,
                timestamp=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error al registrar auditoría: {e}")
            
    # --- 2. MÉTRICAS ---
    @staticmethod
    def obtener_metricas():
        return {
            "donantes": Usuario.query.filter_by(rol='donante').count(),
            "fundaciones": Fundacion.query.count(),
            "pendientes": Fundacion.query.filter_by(estado='pendiente').count(),
            "donaciones": Donacion.query.count(), # Cambiado para contar donaciones reales
            "pagos": Donacion.query.count()
        }

    # --- 3. LISTADOS ENRIQUECIDOS ---
    @staticmethod
    def obtener_listado_donantes():
        return Usuario.query.filter_by(rol='donante').all()
    
    @staticmethod
    def obtener_listado_fundaciones():
        return Fundacion.query.all()
    
    @staticmethod
    def obtener_listado_donaciones_completas():
        return db.session.query(
            Donacion, 
            Usuario.nombre.label('donante_nombre'),
            Fundacion.nombre_fundacion.label('fundacion_nombre'),
            Necesidad.titulo.label('necesidad_titulo'),
            Necesidad.monto_objetivo.label('cantidad_necesidad') 
        ).join(Usuario, Donacion.donante_id == Usuario.id)\
         .join(Necesidad, Donacion.necesidad_id == Necesidad.id)\
         .join(Fundacion, Necesidad.fundacion_id == Fundacion.id).all()