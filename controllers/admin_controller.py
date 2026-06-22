from flask import jsonify, render_template, request, session, send_file, url_for

from controllers import admin_bp
from decorators import admin_required
from models.admin_manager import AdminManager
from models.models import Usuario
from email_service import EmailService
from reporte_pdf import generar_reporte_multi_seccion, filtrar_donaciones, ETIQUETAS_SECCION


# ── Motivos de eliminación para FUNDACIONES (rol institucional) ──
MOTIVOS_ELIMINACION = {
    "INCUMPLIMIENTO": "Incumplimiento de terminos y condiciones",
    "ACTIVIDAD_SOSPECHOSA": "Actividad sospechosa o fraudulenta",
    "SOLICITUD_BAJA": "Solicitud voluntaria de baja",
    "DOCUMENTACION_INVALIDA": "Documentacion legal invalida o vencida"
}

# ── Motivos de eliminación para DONANTES (rol individual) ──
MOTIVOS_ELIMINACION_DONANTE = {
    "CONDUCTA_ABUSIVA": "Conducta abusiva o irrespetuosa en la plataforma",
    "ACTIVIDAD_SOSPECHOSA": "Actividad sospechosa o fraudulenta",
    "SOLICITUD_BAJA": "Solicitud voluntaria de baja de cuenta",
    "CUENTA_DUPLICADA": "Cuenta duplicada o datos inconsistentes"
}


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Obtener listado
    lista_fundaciones = AdminManager.obtener_listado_fundaciones()

    # ── Usuario admin real en sesión (NO confundir con 'fundacion', que
    # es residual y solo apunta a la primera fundación de la lista) ──
    admin_actual = Usuario.query.get(session.get('usuario_id'))

    # Renderizar plantilla correctamente
    return render_template(
        'admin_dashboard.html',
        admin=admin_actual,
        fundacion=lista_fundaciones[0] if lista_fundaciones else None,
        metricas=AdminManager.obtener_metricas(),
        donantes=AdminManager.obtener_listado_donantes(),
        fundaciones=lista_fundaciones,
        fundaciones_pendientes=AdminManager.obtener_fundaciones_pendientes(),
        donaciones=AdminManager.obtener_listado_donaciones_completas(),
        pagos=AdminManager.obtener_pagos(),
        motivos_eliminacion=MOTIVOS_ELIMINACION,
        motivos_eliminacion_donante=MOTIVOS_ELIMINACION_DONANTE
    )
    

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


# =========================
# ELIMINAR FUNDACIÓN (NUEVO)
# =========================
@admin_bp.route('/eliminar_fundacion/<int:fundacion_id>', methods=['POST'])
@admin_required
def eliminar_fundacion(fundacion_id):
    """
    Suspende la fundación (no se borra de la BD, por trazabilidad) y
    notifica por correo el motivo seleccionado por el administrador.
    Espera JSON: { "motivo": "CLAVE_MOTIVO", "mensaje": "texto libre si es OTROS" }
    """
    data = request.get_json(silent=True) or {}
    clave_motivo = data.get('motivo', '')
    mensaje_libre = data.get('mensaje', '').strip()

    if not clave_motivo:
        return jsonify({"success": False, "error": "Debes seleccionar un motivo."}), 400

    if clave_motivo == 'OTROS':
        if not mensaje_libre:
            return jsonify({"success": False, "error": "Debes especificar el motivo."}), 400
        motivo_final = mensaje_libre
    else:
        motivo_final = MOTIVOS_ELIMINACION.get(clave_motivo, clave_motivo)

    exito, mensaje = AdminManager.validar_fundacion(fundacion_id, 'suspendida', motivo_final)
    status_code = 200 if exito else 400
    return jsonify({"success": exito, "mensaje": mensaje}), status_code


# =========================
# ELIMINAR DONANTE (NUEVO)
# =========================
@admin_bp.route('/eliminar_donante/<int:donante_id>', methods=['POST'])
@admin_required
def eliminar_donante(donante_id):
    """
    Da de baja al donante y lo notifica por correo con el motivo
    seleccionado por el administrador.
    Espera JSON: { "motivo": "CLAVE_MOTIVO", "mensaje": "texto libre si es OTROS" }
    """
    data = request.get_json(silent=True) or {}
    clave_motivo = data.get('motivo', '')
    mensaje_libre = data.get('mensaje', '').strip()

    if not clave_motivo:
        return jsonify({"success": False, "error": "Debes seleccionar un motivo."}), 400

    if clave_motivo == 'OTROS':
        if not mensaje_libre:
            return jsonify({"success": False, "error": "Debes especificar el motivo."}), 400
        motivo_final = mensaje_libre
    else:
        motivo_final = MOTIVOS_ELIMINACION_DONANTE.get(clave_motivo, clave_motivo)

    exito, mensaje = AdminManager.dar_baja_donante(donante_id, motivo_final)
    status_code = 200 if exito else 400
    return jsonify({"success": exito, "mensaje": mensaje}), status_code


def _resolver_secciones(valor_seccion):
    """
    Convierte el valor del <select> en una lista de claves de sección.
    'todos' expande a las 5 secciones; cualquier otro valor es una sola.
    """
    valor_seccion = (valor_seccion or "donaciones").strip().lower()
    if valor_seccion == "todos":
        return ["donantes", "fundaciones", "donaciones", "pagos", "pendientes"]
    if valor_seccion in ETIQUETAS_SECCION:
        return [valor_seccion]
    return ["donaciones"]


def _construir_datos_para_secciones(secciones, filtros):
    """
    Obtiene de AdminManager únicamente los datos de las secciones
    pedidas, evitando consultas innecesarias a la base de datos.
    """
    datos = {}

    if "donantes" in secciones:
        datos["donantes"] = AdminManager.obtener_listado_donantes()

    if "fundaciones" in secciones:
        datos["fundaciones"] = AdminManager.obtener_listado_fundaciones()

    if "pendientes" in secciones:
        datos["pendientes"] = AdminManager.obtener_fundaciones_pendientes()

    if "donaciones" in secciones:
        todas = AdminManager.obtener_listado_donaciones_completas()
        datos["donaciones"] = filtrar_donaciones(
            todas,
            categoria=filtros.get("categoria"),
            estado=filtros.get("estado"),
            donante=filtros.get("donante"),
            fundacion=filtros.get("fundacion"),
        )

    if "pagos" in secciones:
        datos["pagos"] = AdminManager.obtener_pagos()

    return datos


def _leer_filtros_request():
    return {
        "seccion": request.args.get("seccion") or request.form.get("seccion") or "donaciones",
        "categoria": request.args.get("categoria") or request.form.get("categoria"),
        "estado": request.args.get("estado") or request.form.get("estado"),
        "donante": request.args.get("donante") or request.form.get("donante"),
        "fundacion": request.args.get("fundacion") or request.form.get("fundacion"),
    }


# =========================
# REPORTE ADMIN: DESCARGA DIRECTA (NUEVO)
# =========================
@admin_bp.route('/api/reporte_admin', methods=['GET'])
@admin_required
def descargar_reporte_admin():
    """
    Genera el PDF en memoria y lo entrega como descarga directa al
    navegador. Soporta el selector de sección (donantes, fundaciones,
    donaciones, pagos, pendientes, o 'todos' para las 5 juntas).
    Solo accesible con sesión de administrador activa.
    """
    filtros = _leer_filtros_request()
    secciones = _resolver_secciones(filtros["seccion"])
    datos = _construir_datos_para_secciones(secciones, filtros)

    buffer = generar_reporte_multi_seccion(secciones, datos)

    etiqueta = filtros["seccion"].lower() if filtros["seccion"] else "donaciones"
    nombre_archivo = f"reporte_red_solidaria_{etiqueta}.pdf"

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nombre_archivo
    )


# =========================
# REPORTE ADMIN: ENVÍO POR CORREO (NUEVO)
# =========================
@admin_bp.route('/api/reporte_admin', methods=['POST'])
@admin_required
def enviar_reporte_admin():
    """
    Envía un correo con un enlace protegido por sesión que, al hacer
    clic, descarga el PDF del reporte de la sección elegida. El PDF
    NUNCA viaja adjunto en el correo: solo se genera cuando el
    administrador hace clic en el enlace estando logueado.
    """
    correo_destino = request.form.get('correo_reporte', '').strip()
    if not correo_destino:
        return jsonify({"success": False, "error": "Debes indicar un correo destino."}), 400

    filtros = _leer_filtros_request()
    secciones = _resolver_secciones(filtros["seccion"])
    datos = _construir_datos_para_secciones(secciones, filtros)
    total_registros = sum(len(v) for v in datos.values())

    enlace_descarga = url_for(
        'admin.descargar_reporte_admin',
        seccion=filtros.get('seccion') or 'donaciones',
        categoria=filtros.get('categoria') or '',
        estado=filtros.get('estado') or '',
        donante=filtros.get('donante') or '',
        fundacion=filtros.get('fundacion') or '',
        _external=True
    )

    etiqueta_legible = (
        "Reporte General (todas las secciones)" if filtros["seccion"] == "todos"
        else f"Reporte de {ETIQUETAS_SECCION.get(filtros['seccion'], filtros['seccion'])}"
    )

    html_content = f"""
    <html><body style="font-family: Arial, sans-serif;">
        <h3>{etiqueta_legible} - Red Solidaria</h3>
        <p>Se generó un reporte con {total_registros} registro(s) en total.</p>
        <p>
            <a href="{enlace_descarga}"
               style="display:inline-block; padding:12px 24px; background:#1e52ff;
                      color:#ffffff; text-decoration:none; border-radius:8px; font-weight:bold;">
                📄 Descargar Reporte PDF
            </a>
        </p>
        <p style="font-size:12px; color:#888;">
            Este enlace requiere que tengas una sesión activa de administrador
            en Red Solidaria. Si no puedes acceder, inicia sesión primero y
            luego haz clic nuevamente en el enlace.
        </p>
    </body></html>
    """

    exito, mensaje = EmailService.enviar_notificacion(
        email_destino=correo_destino,
        nombre_destino="Administrador",
        asunto="Tu Reporte Ejecutivo de Red Solidaria está listo",
        html_content=html_content
    )

    if exito:
        return jsonify({"success": True, "mensaje": "Reporte enviado correctamente al correo indicado."})
    return jsonify({"success": False, "error": mensaje}), 500