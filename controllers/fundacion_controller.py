from flask import flash, redirect, render_template, request, session, url_for

from controllers import fundacion_bp
from decorators import login_required
from models.soporte_manager import SoporteManager
from services.fundacion_service import FundacionService
from reporte_pdf import generar_y_enviar_pdf # Importado desde la raíz

@fundacion_bp.route('/dashboard-fundacion', methods=['GET'])
@login_required
def dashboard_fundacion():
    # 1. Lógica para el botón de Despachar Reporte
    accion = request.args.get('accion')
    email_reporte = request.args.get('correo_reporte')

    if accion == 'reporte' and email_reporte:
        try:
            # Reutilizamos la misma lógica que obtiene el dashboard para generar el reporte
            # Obtenemos los mismos datos que se pasan al template
            _, _, contexto = FundacionService.obtener_dashboard(session.get('usuario_id'))
            
            # Ajusta 'donaciones' o 'necesidades' según lo que contenga tu objeto contexto
            datos_reporte = contexto.get('donaciones', []) 
            
            generar_y_enviar_pdf(datos_reporte, email_reporte)
            flash(f"Reporte enviado exitosamente a {email_reporte}", "success")
            return redirect(url_for('fundacion.dashboard_fundacion'))
        except Exception as e:
            flash(f"Error al enviar el reporte: {str(e)}", "danger")

    # 2. Lógica original de carga de filtros y datos
    q_filtro = request.args.get('q', '').strip() or None
    donante_filtro = request.args.get('donante', '').strip() or None
    categoria_filtro = request.args.get('categoria', '').strip() or None
    estado_filtro = request.args.get('est', '').strip() or None

    exito, mensaje, contexto = FundacionService.obtener_dashboard(
        session.get('usuario_id'),
        q=q_filtro,
        donante=donante_filtro,
        categoria=categoria_filtro,
        est=estado_filtro
    )

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


@fundacion_bp.route('/solicitudes-completo')
@login_required
def solicitudes_fundacion_completo():
    # Renderiza la vista del historial completo de solicitudes
    return render_template('solicitudes_completo.html')