from flask import render_template, request, jsonify, session
from datetime import datetime
from . import admin_bp
from models import db, Fundacion, Usuario, Donacion, Necesidad
from decorators import admin_required 
from admin_manager import AdminManager
from email_service import EmailService

# --- VISTA PRINCIPAL ---
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin_dashboard.html', metricas=AdminManager.obtener_metricas())

# --- ENDPOINTS DE CARGA DINÁMICA ---
@admin_bp.route('/admin/get_<tipo>')
@admin_required
def get_data(tipo):
    if tipo == 'donantes':
        return render_template('partials/tabla_donantes.html', donantes=AdminManager.obtener_listado_donantes())
    elif tipo == 'fundaciones':
        return render_template('partials/tabla_fundaciones.html', fundaciones=AdminManager.obtener_listado_fundaciones())
    elif tipo == 'pendientes':
        return render_template('partials/tabla_pendientes.html', pendientes=Fundacion.query.filter_by(estado='pendiente').all())
    elif tipo == 'donaciones':
        return render_template('partials/tabla_donaciones.html', donaciones=AdminManager.obtener_listado_donaciones_completas())
    elif tipo == 'pagos':
        return render_template('partials/tabla_pagos.html', pagos=Donacion.query.all())
    return jsonify({"error": "Módulo no encontrado"}), 404


# --- PROCESAMIENTO CENTRALIZADO ---
@admin_bp.route('/admin/procesar_accion', methods=['POST'])
@admin_required
def procesar_accion():
    tipo = request.form.get('tipo')
    id_afectado = request.form.get('id')
    motivo = request.form.get('motivo', 'Sin motivo')
    detalle = request.form.get('motivo_otro', '')
    motivo_final = f"{motivo} - {detalle}" if detalle else motivo
    
    # Obtenemos el ID de sesión aquí, arriba, para asegurar que existe
    admin_id = session.get('user_id')

    try:
        if tipo == 'rechazar_fundacion':
            fundacion = Fundacion.query.get_or_404(id_afectado)
            fundacion.estado = 'rechazada'
            db.session.commit()
            
            # Solo intentamos auditoría si tenemos admin_id
            if admin_id:
                AdminManager.registrar_auditoria(f'Fundacion:{id_afectado}', 'RECHAZAR', motivo_final)
            
            if hasattr(fundacion, 'usuario') and fundacion.usuario:
                EmailService.enviar_notificacion(fundacion.usuario.email, fundacion.usuario.nombre, "Actualización", f"Motivo: {motivo_final}")
        
        elif tipo == 'eliminar_donante':
            usuario = Usuario.query.get_or_404(id_afectado)
            usuario.estado = 'suspendido'
            db.session.commit()
            
            if admin_id:
                AdminManager.registrar_auditoria(f'Usuario:{id_afectado}', 'ELIMINAR', motivo_final)
            
            EmailService.enviar_notificacion(usuario.email, usuario.nombre, "Notificación", f"Motivo: {motivo_final}")

        elif tipo == 'aprobar_fundacion':
            fundacion = Fundacion.query.get_or_404(id_afectado)
            fundacion.es_verificado = True
            fundacion.estado = 'activa'
            fundacion.fecha_aprobacion = datetime.utcnow()
            db.session.commit()
            
            # Solo intentamos auditoría si tenemos admin_id
            if admin_id:
                AdminManager.registrar_auditoria(f'Fundacion:{id_afectado}', 'APROBAR', 'Aprobación Administrativa')
            
            try:
                if hasattr(fundacion, 'usuario') and fundacion.usuario:
                    EmailService.enviar_notificacion(fundacion.usuario.email, fundacion.usuario.nombre, "Aprobación", "Tu fundación ha sido activada.")
            except Exception as e:
                print(f"Error al enviar email: {e}")
            
        else:
            return jsonify({"success": False, "message": "Acción no reconocida"}), 400

        return jsonify({"success": True, "message": "Acción procesada correctamente"})
        
    except Exception as e:
        db.session.rollback()
        # Imprimimos el error real en logs de Render para que sepas qué pasó
        print(f"Error completo en procesar_accion: {str(e)}")
        return jsonify({"success": False, "message": f"Error interno: {str(e)}"}), 500