from flask import render_template, redirect, url_for, flash
from . import admin_bp  # Asegúrate de crear admin_bp en tu __init__.py
from database import get_db_connection
from decorators import admin_required

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    # Traemos solo las que no están validadas
    cur.execute("SELECT id, nombre_fundacion, nit FROM fundaciones WHERE es_verificado = FALSE")
    pendientes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin_dashboard.html', pendientes=pendientes)

@admin_bp.route('/aprobar/<int:fundacion_id>', methods=['POST'])
@admin_required
def aprobar(fundacion_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE fundaciones SET es_verificado = TRUE WHERE id = %s", (fundacion_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Fundación aprobada exitosamente.", "success")
    return redirect(url_for('admin_bp.dashboard'))