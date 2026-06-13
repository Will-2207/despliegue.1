from flask import render_template, redirect, url_for, flash, session, request
from . import admin_bp
from models import db, Fundacion, Usuario, Donacion
from decorators import admin_required 
from admin_manager import AdminManager
from email_service import EmailService

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    metricas = AdminManager.obtener_metricas()
    donantes = AdminManager.obtener_listado_donantes()
    fundaciones = AdminManager.obtener_listado_fundaciones()
    donaciones = AdminManager.obtener_listado_donaciones_completas()
    pendientes = Fundacion.query.filter_by(estado='pendiente').all()
    
    return render_template('admin_dashboard.html', 
                           metricas=metricas, 
                           donantes=donantes,
                           fundaciones=fundaciones,
                           donaciones=donaciones,
                           pendientes=pendientes)

@admin_bp.route('/aprobar/<int:fundacion_id>', methods=['POST'])
@admin_required
def aprobar(fundacion_id):
    fundacion = Fundacion.query.get_or_404(fundacion_id)
    fundacion.es_verificado = True
    fundacion.estado = 'activa'
    
    usuario = Usuario.query.get(fundacion.usuario_id)
    if usuario:
        usuario.estado_validacion = 'aprobado'
        
    db.session.commit()
    
    AdminManager.registrar_auditoria(session['usuario_id'], 'APROBAR_FUNDACION', f'Fundacion:{fundacion_id}', 'Aprobación administrativa')
    
    flash("Fundación aprobada exitosamente.", "success")
    return redirect(url_for('admin_bp.dashboard'))

@admin_bp.route('/rechazar-fundacion/<int:id>', methods=['POST'])
@admin_required
def rechazar_fundacion(id):
    motivo_tipo = request.form.get('motivo_tipo', 'Otro')
    motivo_detalle = request.form.get('motivo', '')
    motivo_final = f"{motivo_tipo} - Detalle: {motivo_detalle}" if motivo_detalle else motivo_tipo
    
    fundacion = Fundacion.query.get_or_404(id)
    fundacion.estado = 'rechazada'
    db.session.commit()
    
    AdminManager.registrar_auditoria(session['usuario_id'], 'RECHAZAR_FUNDACION', f'Fundacion:{id}', motivo_final)
    
    # Notificación Brevo
    EmailService.enviar_notificacion(
        fundacion.usuario.email, fundacion.usuario.nombre, 
        "Actualización sobre tu Fundación", 
        f"Tu fundación ha sido rechazada. Motivo: {motivo_final}"
    )
    
    flash("Fundación rechazada y donante notificado.", "info")
    return redirect(url_for('admin_bp.dashboard'))

@admin_bp.route('/eliminar-donante/<int:donante_id>', methods=['POST'])
@admin_required
def eliminar_donante(donante_id):
    # 1. Captura de motivos
    motivo_tipo = request.form.get('motivo_tipo', 'Otro')
    motivo_detalle = request.form.get('motivo', '')
    motivo_final = f"{motivo_tipo} - Detalle: {motivo_detalle}" if motivo_detalle else motivo_tipo
    
    usuario = Usuario.query.get_or_404(donante_id)
    
    # 2. Lógica de suspensión
    usuario.estado = 'suspendido'
    db.session.commit()
    
    # 3. Auditoría
    AdminManager.registrar_auditoria(
        session['usuario_id'], 
        'ELIMINAR_DONANTE', 
        f'Usuario:{donante_id}', 
        motivo_final
    )
    
    # 4. Notificación Brevo
    mensaje = f"Lamentamos informarte que tu cuenta ha sido suspendida. Motivo: {motivo_final}. Si consideras que es un error, contáctanos."
    EmailService.enviar_notificacion(usuario.email, usuario.nombre, "Notificación de cuenta", mensaje)
    
    flash("Donante suspendido y notificado correctamente.", "warning")
    return redirect(url_for('admin_bp.dashboard'))