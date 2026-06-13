from flask import render_template, redirect, url_for, flash
from . import admin_bp  # Asegúrate de crear admin_bp en tu __init__.py
from models import db, Fundacion, Usuario  # Importamos la base de datos y los modelos
# Nota: Si dejaste el decorador admin_required dentro de models.py, cámbialo a: from models import admin_required
from decorators import admin_required 

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Usamos SQLAlchemy para traer las fundaciones no validadas
    pendientes = Fundacion.query.filter_by(es_verificado=False).all()
    
    return render_template('admin_dashboard.html', pendientes=pendientes)

@admin_bp.route('/aprobar/<int:fundacion_id>', methods=['POST'])
@admin_required
def aprobar(fundacion_id):
    # 1. Buscamos la fundación directamente por su ID
    fundacion = Fundacion.query.get_or_404(fundacion_id)
    
    # 2. Marcamos la fundación como verificada
    fundacion.es_verificado = True
    
    # 3. Buscamos al usuario dueño de la fundación y también lo aprobamos
    usuario = Usuario.query.get(fundacion.usuario_id)
    if usuario:
        usuario.estado_validacion = 'aprobado'
        
    # 4. Guardamos todos los cambios en la base de datos
    db.session.commit()
    
    flash("Fundación aprobada exitosamente.", "success")
    return redirect(url_for('admin_bp.dashboard'))