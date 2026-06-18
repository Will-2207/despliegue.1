from flask import flash, redirect, render_template, request, session, url_for

from controllers import fundacion_bp
from decorators import login_required
from models.soporte_manager import SoporteManager
from services.fundacion_service import FundacionService


@fundacion_bp.route('/dashboard-fundacion')
@login_required
def dashboard_fundacion():
    exito, mensaje, contexto = FundacionService.obtener_dashboard(session.get('usuario_id'))

    if not exito:
        session.clear()
        flash(mensaje, "warning")
        return redirect(url_for('auth.login'))

    return render_template('dashboard_fundacion.html', **contexto)


@fundacion_bp.route('/publicar-necesidad', methods=['GET', 'POST'])
@login_required
def publicar_necesidad():
    if not FundacionService.puede_acceder(session.get('usuario_id')):
        session.clear()
        flash("Tu fundacion aun no esta aprobada para publicar necesidades.", "warning")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        exito, mensaje = FundacionService.publicar_necesidad(
            session.get('usuario_id'),
            request.form
        )
        flash(mensaje, 'success' if exito else 'danger')

        if exito:
            return redirect(url_for('fundacion.dashboard_fundacion'))

    return render_template('publicar_necesidad.html')


@fundacion_bp.route('/soporte', methods=['GET', 'POST'])
@login_required
def soporte():
    resultado = None
    if request.method == 'POST':
        resultado = SoporteManager.procesar_soporte(request.form)
    return render_template('soporte.html', resultado=resultado)
