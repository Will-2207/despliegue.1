from flask import jsonify, render_template, request

from controllers import admin_bp
from decorators import admin_required
from models.admin_manager import AdminManager


MOTIVOS_ELIMINACION = {
    "INCUMPLIMIENTO": "Incumplimiento de terminos y condiciones",
    "ACTIVIDAD_SOSPECHOSA": "Actividad sospechosa o fraudulenta",
    "SOLICITUD_BAJA": "Solicitud voluntaria de baja",
    "DOCUMENTACION_INVALIDA": "Documentacion legal invalida o vencida"
}


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin_dashboard.html', metricas=AdminManager.obtener_metricas())


@admin_bp.route('/get_<tipo>')
@admin_required
def get_data(tipo):
    if tipo == 'donantes':
        return render_template(
            'partials/tabla_donantes.html',
            donantes=AdminManager.obtener_listado_donantes()
        )

    if tipo == 'fundaciones':
        return render_template(
            'partials/tabla_fundaciones.html',
            fundaciones=AdminManager.obtener_listado_fundaciones(),
            motivos_eliminacion=MOTIVOS_ELIMINACION
        )

    if tipo == 'pendientes':
        return render_template(
            'partials/tabla_pendientes.html',
            pendientes=AdminManager.obtener_fundaciones_pendientes(),
            motivos_eliminacion=MOTIVOS_ELIMINACION
        )

    if tipo == 'donaciones':
        return render_template(
            'partials/tabla_donaciones.html',
            donaciones=AdminManager.obtener_listado_donaciones_completas()
        )

    if tipo == 'pagos':
        return render_template(
            'partials/tabla_pagos.html',
            pagos=AdminManager.obtener_pagos()
        )

    return jsonify({"error": "Modulo no encontrado"}), 404


@admin_bp.route('/procesar_accion', methods=['POST'])
@admin_required
def procesar_accion():
    tipo = request.form.get('tipo')
    id_af = request.form.get('id')
    motivo_seleccionado = request.form.get('motivo', '')
    motivo_otro = request.form.get('motivo_otro', '')
    motivo = f"{motivo_seleccionado} - {motivo_otro}".strip(" -")

    mapping = {
        'aprobar_fundacion': 'activa',
        'rechazar_fundacion': 'rechazada',
        'eliminar_fundacion': 'suspendida'
    }

    if tipo not in mapping:
        return jsonify({"success": False, "message": "Accion no reconocida"}), 400

    exito, mensaje = AdminManager.validar_fundacion(id_af, mapping[tipo], motivo)
    status_code = 200 if exito else 400
    return jsonify({"success": exito, "message": mensaje}), status_code
