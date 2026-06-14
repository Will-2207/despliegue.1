from flask import session, request
from datetime import datetime
from models import db, Usuario, Fundacion, Necesidad, Donacion, Auditoria

class AdminManager:
    
    @staticmethod
    def registrar_auditoria(recurso_afectado, accion, motivo):
        # 1. Obtenemos el ID de sesión
        admin_id = session.get('user_id')
        
        # 2. SI EL ID ES NULO, FORZAMOS UN VALOR O LOGUEAMOS EL ERROR
        # Esto evita que falle la base de datos con el error NotNullViolation
        if admin_id is None:
            print("ADVERTENCIA: Se intentó registrar auditoría sin sesión de admin. Usando ID 1 por defecto.")
            admin_id = 1 # O el ID del admin principal que tengas en tu BD
            
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