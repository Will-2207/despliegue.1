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
    # Convertimos la cantidad a int aquí mismo para evitar errores de tipo
    try:
        cantidad = int(request.form.get('cantidad', 0))
    except ValueError:
        flash("La cantidad debe ser un número válido.", "danger")
        return redirect(url_for('donaciones_bp.donante'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT fundacion_id, categoria FROM necesidades WHERE id = %s", (necesidad_id,))
    nec = cur.fetchone()
    cur.close()
    conn.close()
    
    if nec:
        # Aquí capturamos el éxito y el mensaje real del manager
        exito, mensaje = NecesidadesManager.registrar_donacion_fisica(
            necesidad_id, session['usuario_id'], nec['fundacion_id'], nec['categoria'], cantidad
        )
        
        if exito:
            flash(mensaje, "success")
        else:
            flash(mensaje, "danger") # Esto mostrará el error específico del manager
    else:
        flash("La necesidad no existe.", "danger")
            
    return redirect(url_for('donaciones_bp.donante'))