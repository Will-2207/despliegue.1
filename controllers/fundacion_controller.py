from flask import render_template, request, session, redirect, url_for, flash
from . import fundacion_bp
from database import get_db_connection
from necesidades_manager import NecesidadesManager
from soporte_manager import SoporteManager
from decorators import login_required  # Importamos el decorador
import json

@fundacion_bp.route('/dashboard-fundacion')
@login_required
def dashboard_fundacion():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM fundaciones WHERE usuario_id = %s", (session['usuario_id'],))
    res = cur.fetchone()
    cur.close()
    conn.close()
    
    if not res: 
        flash("Acceso denegado: No eres una fundación registrada.", "danger")
        return redirect(url_for('donaciones_bp.donante'))
    
    fundacion_id = res[0]
    donaciones = NecesidadesManager.obtener_donaciones_por_fundacion(fundacion_id)
    return render_template('dashboard_fundacion.html', donaciones=donaciones)

@fundacion_bp.route('/publicar-necesidad', methods=['GET', 'POST'])
@login_required
def publicar_necesidad():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM fundaciones WHERE usuario_id = %s", (session['usuario_id'],))
    fundacion = cur.fetchone()
    cur.close()
    conn.close()
    
    if not fundacion:
        flash("Solo las fundaciones pueden publicar necesidades.", "danger")
        return redirect(url_for('donaciones_bp.donante'))
        
    if request.method == 'POST':
        # 1. Extraemos los campos base
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        cantidad = request.form.get('cantidad_requerida')
        categoria = request.form.get('categoria')
        fecha_limite = request.form.get('fecha_limite')
        
        # 2. Construimos el diccionario de detalles específicos
        detalles = {k: v for k, v in request.form.items() if k not in 
                    ['titulo', 'descripcion', 'cantidad_requerida', 'categoria', 'fecha_limite']}
        
        # 3. Llamamos al manager
        if NecesidadesManager.crear_necesidad(fundacion[0], titulo, descripcion, cantidad, categoria, fecha_limite, detalles):
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