from flask import render_template, request, session, redirect, url_for, flash
from . import fundacion_bp
from models import db, Usuario, Fundacion, Necesidad, Donacion
from necesidades_manager import NecesidadesManager
from soporte_manager import SoporteManager
from decorators import login_required

@fundacion_bp.route('/dashboard-fundacion')
@login_required
def dashboard_fundacion():
    # 1. Buscamos el usuario y su fundación usando SQLAlchemy
    usuario = Usuario.query.get(session.get('usuario_id'))
    fundacion = Fundacion.query.filter_by(usuario_id=usuario.id).first()
    
    if not fundacion:
        flash("Acceso denegado: No eres una fundación registrada.", "danger")
        return redirect(url_for('donaciones_bp.donante'))
    
    # 2. Obtenemos las donaciones haciendo JOIN con SQLAlchemy
    donaciones = db.session.query(
        Donacion.created_at,
        Donacion.monto,
        Necesidad.titulo.label('titulo_necesidad'),
        Usuario.nombre.label('nombre_donante')
    ).join(Necesidad, Donacion.necesidad_id == Necesidad.id)\
     .join(Usuario, Donacion.donante_id == Usuario.id)\
     .filter(Necesidad.fundacion_id == fundacion.id)\
     .order_by(Donacion.created_at.desc()).all()

    return render_template('dashboard_fundacion.html', 
                           usuario=usuario, 
                           fundacion=fundacion, 
                           donaciones=donaciones)

@fundacion_bp.route('/publicar-necesidad', methods=['GET', 'POST'])
@login_required
def publicar_necesidad():
    # Buscamos la fundación del usuario actual con SQLAlchemy
    usuario_id = session.get('usuario_id')
    fundacion = Fundacion.query.filter_by(usuario_id=usuario_id).first()
    
    if not fundacion:
        flash("Solo las fundaciones pueden publicar necesidades.", "danger")
        return redirect(url_for('donaciones_bp.donante'))
        
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        cantidad = request.form.get('cantidad_requerida')
        categoria = request.form.get('categoria')
        fecha_limite = request.form.get('fecha_limite')
        
        # Recolectamos detalles adicionales (todo lo que no sean los campos básicos)
        detalles = {k: v for k, v in request.form.items() if k not in 
                    ['titulo', 'descripcion', 'cantidad_requerida', 'categoria', 'fecha_limite']}
        
        # Usamos la lógica de tu Manager, pasando el ID de la fundación encontrada
        if NecesidadesManager.crear_necesidad(fundacion.id, titulo, descripcion, cantidad, categoria, fecha_limite, detalles):
            flash("¡Necesidad publicada exitosamente!", "success")
        else:
            flash("Error al publicar la necesidad.", "danger")
            
        return redirect(url_for('fundacion_bp.dashboard_fundacion'))
        
    return render_template('publicar_necesidad.html')

@fundacion_bp.route('/soporte', methods=['GET', 'POST'])
@login_required
def soporte():
    resultado = None
    if request.method == 'POST':
        resultado = SoporteManager.procesar_soporte(request.form)
    return render_template('soporte.html', resultado=resultado)