from models import db, Usuario, Fundacion, Necesidad, Donacion, Auditoria
from flask import request
from datetime import datetime

class AdminManager:
    
    # --- 1. LÓGICA DE AUDITORÍA (Seguridad) ---
    @staticmethod
    def registrar_auditoria(admin_id, accion, recurso_afectado, motivo=None):
        """Registra cada acción administrativa realizada en el sistema."""
        nueva_auditoria = Auditoria(
            admin_id=admin_id,
            accion=accion,
            recurso_afectado=recurso_afectado,
            motivo=motivo,
            ip=request.remote_addr,
            timestamp=datetime.utcnow()
        )
        db.session.add(nueva_auditoria)
        db.session.commit()

    # --- 2. LÓGICA DE MÉTRICAS (Dashboard) ---
    @staticmethod
    def obtener_metricas():
        """Retorna un diccionario con los contadores dinámicos."""
        return {
            "total_donantes": Usuario.query.filter_by(rol='donante').count(),
            "total_fundaciones": Fundacion.query.count(),
            "fundaciones_pendientes": Fundacion.query.filter_by(estado='pendiente').count(),
            "donaciones_activas": Necesidad.query.filter_by(estado='activa').count(),
            "total_pagos": Donacion.query.count()
        }

    # --- 3. LÓGICA DE LISTADOS (Data tables) ---
    @staticmethod
    def obtener_listado_donantes():
        return Usuario.query.filter_by(rol='donante').all()

    @staticmethod
    def obtener_listado_fundaciones():
        return Fundacion.query.all()

    @staticmethod
    def obtener_listado_donaciones_completas():
        # Retorna donaciones con info relacionada para la tabla
        return db.session.query(
            Donacion, 
            Usuario.nombre.label('donante_nombre'),
            Fundacion.nombre_fundacion.label('fundacion_nombre'),
            Necesidad.titulo.label('necesidad_titulo')
        ).join(Usuario, Donacion.donante_id == Usuario.id)\
         .join(Necesidad, Donacion.necesidad_id == Necesidad.id)\
         .join(Fundacion, Necesidad.fundacion_id == Fundacion.id).all()