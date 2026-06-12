from flask import render_template, session, redirect, url_for, flash, request
from . import donaciones_bp
from necesidades_manager import NecesidadesManager
from database import get_db_connection
from psycopg2.extras import RealDictCursor
from decorators import login_required  # Importamos el decorador
import traceback  # Asegúrate de importar esto arriba

@donaciones_bp.route('/donante')
@login_required
def donante():
    try:
        necesidades = NecesidadesManager.obtener_necesidades_activas()
        return render_template('donante.html', necesidades=necesidades)
    except Exception as e:
        # ESTO ES LO QUE NECESITAMOS:
        print("--- ERROR DETECTADO EN /donante ---")
        traceback.print_exc() 
        print("-----------------------------------")
        return render_template('error.html', mensaje_error="No pudimos cargar las causas."), 500
    
    
@donaciones_bp.route('/mis-donaciones')
@login_required
def mis_donaciones():
    mis_donaciones = NecesidadesManager.obtener_mis_donaciones(session['usuario_id'])
    return render_template('mis_donaciones.html', donaciones=mis_donaciones)

@donaciones_bp.route('/donar-fisica', methods=['POST'])
@login_required
def donar_fisica():
    necesidad_id = request.form.get('necesidad_id')
    cantidad = request.form.get('cantidad')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT fundacion_id, categoria FROM necesidades WHERE id = %s", (necesidad_id,))
    nec = cur.fetchone()
    cur.close()
    conn.close()
    
    if nec:
        if NecesidadesManager.registrar_donacion_fisica(necesidad_id, session['usuario_id'], nec['fundacion_id'], nec['categoria'], cantidad):
            flash("¡Gracias por tu donación física!", "success")
        else:
            flash("Error al registrar la donación.", "danger")
            
    return redirect(url_for('donaciones_bp.donante'))