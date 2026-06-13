from flask import render_template, redirect, url_for, flash
from . import admin_bp
from models import db, Fundacion, Usuario
from decorators import admin_required 

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    pendientes = Fundacion.query.filter_by(es_verificado=False).all()
    return render_template('admin_dashboard.html', pendientes=pendientes)

@admin_bp.route('/aprobar/<int:fundacion_id>', methods=['POST'])
@admin_required
def aprobar(fundacion_id):
    fundacion = Fundacion.query.get_or_404(fundacion_id)
    fundacion.es_verificado = True
    
    usuario = Usuario.query.get(fundacion.usuario_id)
    if usuario:
        usuario.estado_validacion = 'aprobado'
        
    db.session.commit()
    
    flash("Fundación aprobada exitosamente.", "success")
    return redirect(url_for('admin_bp.dashboard'))