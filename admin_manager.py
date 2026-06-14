from flask import session, request
from datetime import datetime
from models import db, Usuario, Fundacion, Necesidad, Donacion, Auditoria

class AdminManager:
    
    # --- 1. AUDITORÍA ---
    @staticmethod
    def registrar_auditoria(recurso, accion, motivo=None):
        log = Auditoria(
            admin_id=session.get('user_id'),
            recurso_afectado=recurso,
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
            "donaciones": Necesidad.query.filter_by(estado='activa').count(),
            "pagos": Donacion.query.count()
        }

    # --- 3. ACCIONES ---
    @staticmethod
    def procesar_rechazo_fundacion(fundacion_id, motivo):
        fundacion = Fundacion.query.get(fundacion_id)
        if fundacion:
            fundacion.estado = 'rechazada' # Usar minúscula para consistencia
            AdminManager.registrar_auditoria(f'Fundacion ID: {fundacion_id}', 'Rechazo', motivo)
            db.session.commit()
            return True
        return False

    @staticmethod
    def eliminar_donante(donante_id, motivo):
        donante = Usuario.query.get(donante_id)
        if donante:
            # Soft delete o estado 'suspendido' en lugar de borrar para mantener historial
            donante.estado = 'suspendido' 
            AdminManager.registrar_auditoria(f'Donante ID: {donante_id}', 'Suspensión', motivo)
            db.session.commit()
            return True
        return False

    # --- 4. LISTADOS ENRIQUECIDOS (Data Completa) ---
    @staticmethod
    def obtener_listado_donantes():
        # Asumiendo que Usuario tiene estos campos en tu modelo
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
            Fundacion.email_contacto.label('fundacion_email'), # Asegúrate que este campo exista
            Necesidad.titulo.label('necesidad_titulo'),
            Necesidad.cantidad_solicitada.label('cantidad_necesidad') # Asegúrate que este campo exista
        ).join(Usuario, Donacion.donante_id == Usuario.id)\
         .join(Necesidad, Donacion.necesidad_id == Necesidad.id)\
         .join(Fundacion, Necesidad.fundacion_id == Fundacion.id).all()