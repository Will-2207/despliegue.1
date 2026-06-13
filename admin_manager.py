from flask import session, request
from datetime import datetime
from models import db, Usuario, Fundacion, Necesidad, Donacion, Auditoria

class AdminManager:
    
    # --- 1. AUDITORÍA Y SEGURIDAD ---
    @staticmethod
    def registrar_auditoria(recurso, accion, motivo=None):
        """Registra toda acción administrativa con IP y timestamp."""
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

    # --- 2. MÉTRICAS DINÁMICAS (Dashboard) ---
    @staticmethod
    def obtener_metricas():
        """Retorna contadores para las tarjetas del Dashboard."""
        return {
            "donantes": Usuario.query.filter_by(rol='donante').count(),
            "fundaciones": Fundacion.query.count(),
            "pendientes": Fundacion.query.filter_by(estado='pendiente').count(),
            "donaciones": Necesidad.query.filter_by(estado='activa').count(),
            "pagos": Donacion.query.count()
        }

    # --- 3. ACCIONES CRÍTICAS (Lógica de negocio) ---
    @staticmethod
    def procesar_rechazo_fundacion(fundacion_id, motivo):
        fundacion = Fundacion.query.get(fundacion_id)
        if fundacion:
            fundacion.estado = 'Rechazada'
            # Aquí integrarías tu: email_service.enviar_notificacion_rechazo(...)
            AdminManager.registrar_auditoria(f'Fundacion ID: {fundacion_id}', 'Rechazo', motivo)
            db.session.commit()
            return True
        return False

    @staticmethod
    def eliminar_donante(donante_id, motivo):
        donante = Usuario.query.get(donante_id)
        if donante:
            # Aquí podrías hacer un soft-delete o borrar
            db.session.delete(donante)
            AdminManager.registrar_auditoria(f'Donante ID: {donante_id}', 'Eliminación', motivo)
            db.session.commit()
            return True
        return False

    # --- 4. LISTADOS PARA TABLAS ---
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
            Necesidad.titulo.label('necesidad_titulo')
        ).join(Usuario, Donacion.donante_id == Usuario.id)\
         .join(Necesidad, Donacion.necesidad_id == Necesidad.id)\
         .join(Fundacion, Necesidad.fundacion_id == Fundacion.id).all()