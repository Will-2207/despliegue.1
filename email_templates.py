"""
Plantillas HTML para los correos de notificación de Red Solidaria.
Usa el mismo estilo visual (degradado azul -> verde, tarjetas redondeadas)
que se usa en donante.html y dashboard_fundacion.html.

IMPORTANTE: los correos no pueden usar url_for() de Flask, por eso el logo
se referencia con la URL pública completa del despliegue en Render.
"""

LOGO_URL = "https://despliegue-1-1s1j.onrender.com/static/perfil_13_Logo.jpeg"

AZUL = "#1e52ff"
VERDE = "#28a745"


def _base_html(titulo_emoji, titulo, nombre_destino, cuerpo_html):
    """
    Estructura base compartida por todos los correos: logo, header con
    degradado, tarjeta blanca con sombra, y pie de página.
    """
    return f"""
    <html>
    <body style="margin:0; padding:0; background-color:#f4f6fa; font-family:'Segoe UI', Arial, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6fa; padding:30px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:24px; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.08);">

                        <!-- Header con degradado de marca -->
                        <tr>
                            <td style="background: linear-gradient(135deg, {AZUL}, {VERDE}); padding:35px; text-align:center;">
                                <img src="{LOGO_URL}" width="90" height="90" alt="Red Solidaria"
                                     style="border-radius:50%; border:4px solid rgba(255,255,255,0.85); object-fit:cover; margin-bottom:14px;">
                                <h2 style="color:#ffffff; margin:0; font-size:22px;">{titulo_emoji} {titulo}</h2>
                            </td>
                        </tr>

                        <!-- Cuerpo -->
                        <tr>
                            <td style="padding:35px;">
                                <p style="font-size:16px; color:#333333; margin-top:0;">Hola, <b>{nombre_destino}</b> 👋</p>
                                {cuerpo_html}
                            </td>
                        </tr>

                        <!-- Pie -->
                        <tr>
                            <td style="background:#f8f9fa; padding:20px 35px; text-align:center; border-top:1px solid #eef2f5;">
                                <p style="font-size:12px; color:#999999; margin:0;">
                                    Este es un mensaje automático de <b>Red Solidaria</b>. Por favor no respondas a este correo.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def _detalle_card(filas):
    """
    Genera una tarjeta gris con pares clave/valor, estilo 'stats-lateral'
    de tus paneles. filas es una lista de tuplas (etiqueta, valor).
    """
    filas_html = ""
    for etiqueta, valor in filas:
        filas_html += f"""
        <tr>
            <td style="padding:8px 0; border-bottom:1px solid #eef2f5; font-size:14px; color:#666;">{etiqueta}</td>
            <td style="padding:8px 0; border-bottom:1px solid #eef2f5; font-size:14px; color:#222; font-weight:bold; text-align:right;">{valor}</td>
        </tr>
        """
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9fa; border-radius:14px; border:1px solid #eef2f5; padding:15px 20px; margin-top:15px;">
        {filas_html}
    </table>
    """


# =========================
# DONACIÓN FÍSICA
# =========================

def correo_donante_fisica(nombre_donante, fundacion_nombre, articulo, cantidad, fecha):
    cuerpo = f"""
    <p style="font-size:15px; color:#555;">
        ¡Gracias por tu generosidad! Tu donación física ha sido registrada exitosamente
        y ya fue notificada a la fundación.
    </p>
    {_detalle_card([
        ("Fundación beneficiada", fundacion_nombre),
        ("Artículo donado", articulo),
        ("Cantidad", cantidad),
        ("Fecha de registro", fecha),
    ])}
    <p style="font-size:13px; color:#999; margin-top:20px;">
        La fundación se pondrá en contacto contigo para coordinar la entrega si es necesario.
    </p>
    """
    return _base_html("📦", "¡Donación Física Registrada!", nombre_donante, cuerpo)


def correo_fundacion_fisica(nombre_fundacion, donante_nombre, articulo, cantidad, fecha):
    cuerpo = f"""
    <p style="font-size:15px; color:#555;">
        Tienes una nueva donación física pendiente de gestión en tu panel. Una persona
        más se ha sumado a tu causa.
    </p>
    {_detalle_card([
        ("Donante", donante_nombre),
        ("Artículo ofrecido", articulo),
        ("Cantidad", cantidad),
        ("Fecha de registro", fecha),
    ])}
    <p style="font-size:13px; color:#999; margin-top:20px;">
        Ingresa a tu panel de fundación para aceptar, rechazar o gestionar esta donación.
    </p>
    """
    return _base_html("📦", "Nueva Donación Física Recibida", nombre_fundacion, cuerpo)


# =========================
# DONACIÓN MONETARIA (CAUSA SOCIAL)
# =========================

def correo_donante_monetaria(nombre_donante, fundacion_nombre, nombre_necesidad, monto, card_brand, card_last4, fecha):
    marca = (card_brand or "tarjeta").capitalize()
    ultimos4 = card_last4 or "****"
    cuerpo = f"""
    <p style="font-size:15px; color:#555;">
        ¡Tu aporte monetario fue procesado exitosamente! Gracias por impulsar esta
        causa social con tu generosidad.
    </p>
    {_detalle_card([
        ("Causa Social", nombre_necesidad or "Causa Social"),
        ("Monto aportado", f"${monto} COP"),
        ("Método de pago", f"💳 {marca} •••• {ultimos4}"),
        ("Fecha de transacción", fecha),
    ])}
    <p style="font-size:13px; color:#999; margin-top:20px;">
        Por seguridad, nunca almacenamos tu número de tarjeta completo. Tu pago fue
        procesado de forma segura a través de Stripe.
    </p>
    """
    return _base_html("💳", f"¡Aporte Confirmado para {fundacion_nombre}!", nombre_donante, cuerpo)


def correo_fundacion_monetaria(nombre_fundacion, donante_nombre, nombre_necesidad, monto, card_brand, card_last4, fecha):
    marca = (card_brand or "tarjeta").capitalize()
    ultimos4 = card_last4 or "****"
    cuerpo = f"""
    <p style="font-size:15px; color:#555;">
        ¡Buenas noticias! Has recibido un nuevo aporte monetario para tu causa social.
    </p>
    {_detalle_card([
        ("Causa Social", nombre_necesidad or "Causa Social"),
        ("Donante", donante_nombre),
        ("Monto recibido", f"${monto} COP"),
        ("Método de pago", f"💳 {marca} •••• {ultimos4}"),
        ("Fecha de transacción", fecha),
    ])}
    <p style="font-size:13px; color:#999; margin-top:20px;">
        Los fondos fueron procesados y conciliados automáticamente a través de Stripe.
    </p>
    """
    return _base_html("💳", "Nuevo Aporte Monetario Recibido", nombre_fundacion, cuerpo)