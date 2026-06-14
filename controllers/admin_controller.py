from flask import render_template, request, jsonify, session
from . import admin_bp
from models import db, Fundacion, Usuario, Donacion
from decorators import admin_required 
from admin_manager import AdminManager
from email_service import EmailService

# --- VISTA PRINCIPAL ---
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin_dashboard.html', metricas=AdminManager.obtener_metricas())

# --- ENDPOINTS DE CARGA DINÁMICA (AJAX) ---
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

# --- PROCESAMIENTO CENTRALIZADO DE ACCIONES ---
@admin_bp.route('/admin/procesar_accion', methods=['POST'])
@admin_required
def procesar_accion():
    tipo = request.form.get('tipo')
    id_afectado = request.form.get('id')
    motivo = request.form.get('motivo', 'Sin motivo')
    detalle = request.form.get('motivo_otro', '')
    motivo_final = f"{motivo} - {detalle}" if detalle else motivo

    try:
        if tipo == 'rechazar_fundacion':
            fundacion = Fundacion.query.get_or_404(id_afectado)
            fundacion.estado = 'rechazada'
            AdminManager.registrar_auditoria(f'Fundacion:{id_afectado}', 'RECHAZAR_FUNDACION', motivo_final)
            EmailService.enviar_notificacion(fundacion.usuario.email, fundacion.usuario.nombre, "Actualización Fundación", f"Motivo: {motivo_final}")
        
        elif tipo == 'eliminar_donante':
            usuario = Usuario.query.get_or_404(id_afectado)
            usuario.estado = 'suspendido'
            AdminManager.registrar_auditoria(f'Usuario:{id_afectado}', 'ELIMINAR_DONANTE', motivo_final)
            EmailService.enviar_notificacion(usuario.email, usuario.nombre, "Notificación de cuenta", f"Cuenta suspendida. Motivo: {motivo_final}")

        elif tipo == 'aprobar_fundacion':
            fundacion = Fundacion.query.get_or_404(id_afectado)
            fundacion.es_verificado = True
            fundacion.estado = 'activa'
            AdminManager.registrar_auditoria(f'Fundacion:{id_afectado}', 'APROBAR_FUNDACION', 'Aprobación Administrativa')
            EmailService.enviar_notificacion(fundacion.usuario.email, fundacion.usuario.nombre, "Aprobación Exitosa", "Tu fundación ha sido activada.")
            
        else:
            return jsonify({"success": False, "message": "Acción no reconocida"}), 400

        db.session.commit()
        return jsonify({"success": True, "message": "Acción procesada correctamente"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error interno: {str(e)}"}), 500