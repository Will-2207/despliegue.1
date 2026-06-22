"""
Generador de reportes PDF para el panel de administración de Red Solidaria.

Usa ReportLab (no WeasyPrint/pdfkit) a propósito: ReportLab dibuja el PDF
directamente con código Python sin levantar ningún motor de renderizado
tipo navegador, lo que mantiene el consumo de RAM mínimo -- importante
porque este proyecto corre en el plan gratuito de Render.

El PDF se genera completamente EN MEMORIA (io.BytesIO), nunca se escribe
a disco, así que tampoco consume espacio de almacenamiento en el servidor.
"""

import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

AZUL = colors.HexColor("#1e52ff")
VERDE = colors.HexColor("#28a745")
GRIS_CLARO = colors.HexColor("#f8f9fa")
GRIS_BORDE = colors.HexColor("#dddddd")

# Etiquetas legibles para cada sección, usadas en el título del PDF
ETIQUETAS_SECCION = {
    "donantes": "Donantes",
    "fundaciones": "Fundaciones",
    "donaciones": "Donaciones",
    "pagos": "Pagos",
    "pendientes": "Fundaciones Pendientes",
}


def _ruta_logo():
    """
    Busca el logo real del proyecto en static/. Si no se encuentra,
    devuelve None y el PDF simplemente no muestra logo (no falla).
    """
    posibles_rutas = [
        os.path.join("static", "perfil_13_Logo.jpeg"),
        os.path.join("static", "Logo.jpeg"),
    ]
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            return ruta
    return None


def _valor(d, campo, default="—"):
    """Lee 'campo' de un Row de SQLAlchemy o de un dict, lo que sea que venga."""
    if isinstance(d, dict):
        val = d.get(campo, default)
    else:
        val = getattr(d, campo, default)
    return val if val is not None else default


def _estilos():
    styles = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "TituloHeader", parent=styles["Title"], textColor=colors.white,
            fontSize=20, spaceAfter=4
        ),
        "subtitulo": ParagraphStyle(
            "SubtituloHeader", parent=styles["Normal"], textColor=colors.white,
            fontSize=10
        ),
        "seccion": ParagraphStyle(
            "Seccion", parent=styles["Heading2"], textColor=AZUL,
            fontSize=13, spaceBefore=14, spaceAfter=8
        ),
    }


def _bloque_encabezado(titulo_texto, estilos):
    """Banner azul con logo (si existe) + título + fecha de generación."""
    logo_path = _ruta_logo()
    logo_cell = Image(logo_path, width=1.1 * cm, height=1.1 * cm) if logo_path else ""

    header_data = [
        [logo_cell, Paragraph(titulo_texto, estilos["titulo"])],
        ["", Paragraph(
            f"Red Solidaria  |  Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            estilos["subtitulo"]
        )],
    ]
    header_table = Table(header_data, colWidths=[1.8 * cm, 15.2 * cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
    ]))
    return header_table


def _tabla_estilizada(tabla_data, col_widths):
    tabla = Table(tabla_data, colWidths=col_widths, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tabla


def _barra_resumen(texto_izquierda, texto_derecha):
    resumen_data = [[texto_izquierda, texto_derecha]]
    resumen_table = Table(resumen_data, colWidths=[8.5 * cm, 8.5 * cm])
    resumen_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
    ]))
    return resumen_table


# =========================
# CONSTRUCCIÓN DE CADA TABLA POR SECCIÓN
# =========================

def _seccion_donantes(elementos, estilos, donantes):
    elementos.append(Paragraph("Donantes Registrados", estilos["seccion"]))
    tabla_data = [["Nombre", "Correo", "Fecha Registro", "Estado"]]
    for d in donantes:
        tabla_data.append([
            str(_valor(d, "nombre")), str(_valor(d, "correo")),
            str(_valor(d, "fecha_registro")), str(_valor(d, "estado")).capitalize()
        ])
    if len(tabla_data) == 1:
        tabla_data.append(["Sin donantes registrados.", "", "", ""])
    elementos.append(_tabla_estilizada(tabla_data, [5 * cm, 6 * cm, 3.5 * cm, 2.5 * cm]))
    elementos.append(Spacer(1, 10))
    elementos.append(_barra_resumen(f"Total de donantes: {len(donantes)}", ""))


def _seccion_fundaciones(elementos, estilos, fundaciones, titulo="Fundaciones Registradas"):
    elementos.append(Paragraph(titulo, estilos["seccion"]))
    tabla_data = [["Nombre", "NIT", "Correo", "Fecha Registro", "Estado"]]
    for f in fundaciones:
        tabla_data.append([
            str(_valor(f, "nombre")), str(_valor(f, "nit")), str(_valor(f, "correo")),
            str(_valor(f, "fecha_registro")), str(_valor(f, "estado_validacion")).capitalize()
        ])
    if len(tabla_data) == 1:
        tabla_data.append(["Sin fundaciones registradas.", "", "", "", ""])
    elementos.append(_tabla_estilizada(tabla_data, [4 * cm, 2.7 * cm, 4.5 * cm, 3 * cm, 2.8 * cm]))
    elementos.append(Spacer(1, 10))
    elementos.append(_barra_resumen(f"Total: {len(fundaciones)}", ""))


def _seccion_donaciones(elementos, estilos, donaciones):
    elementos.append(Paragraph("Detalle de Donaciones", estilos["seccion"]))
    tabla_data = [["Donante", "Fundación", "Necesidad", "Monto / Cantidad", "Fecha", "Estado"]]
    total_monetario = 0.0

    for d in donaciones:
        donante = _valor(d, "donante_nombre", "Anónimo")
        fundacion = _valor(d, "fundacion_nombre")
        necesidad = _valor(d, "necesidad_titulo")
        cantidad = _valor(d, "cantidad_necesidad", None)
        fecha = _valor(d, "fecha_creacion", None)
        estado = _valor(d, "estado_donacion")

        try:
            monto_float = float(cantidad)
            es_monto_dinero = monto_float == int(monto_float) and monto_float > 1000
        except (TypeError, ValueError):
            monto_float = None
            es_monto_dinero = False

        if monto_float is not None and es_monto_dinero:
            valor_mostrado = f"${monto_float:,.0f} COP"
            total_monetario += monto_float
        else:
            valor_mostrado = f"{cantidad} unidades" if cantidad is not None else "—"

        fecha_str = fecha.strftime("%d/%m/%Y") if fecha else "—"

        tabla_data.append([
            str(donante), str(fundacion), str(necesidad)[:25],
            valor_mostrado, fecha_str, str(estado).capitalize()
        ])

    if len(tabla_data) == 1:
        tabla_data.append(["Sin donaciones registradas.", "", "", "", "", ""])

    elementos.append(_tabla_estilizada(
        tabla_data, [2.8 * cm, 3.2 * cm, 3.5 * cm, 3 * cm, 2.2 * cm, 2.3 * cm]
    ))
    elementos.append(Spacer(1, 10))
    elementos.append(_barra_resumen(
        f"Total de registros: {len(donaciones)}",
        f"Total recaudado (monetario): ${total_monetario:,.0f} COP"
    ))


def _seccion_pagos(elementos, estilos, pagos):
    elementos.append(Paragraph("Registro de Pagos (Stripe)", estilos["seccion"]))
    tabla_data = [["ID", "Donante", "Fundación", "Monto", "Fecha", "Estado"]]
    total = 0.0
    for p in pagos:
        monto = _valor(p, "monto", 0)
        try:
            total += float(monto)
            monto_str = f"${float(monto):,.0f} COP"
        except (TypeError, ValueError):
            monto_str = str(monto)
        fecha = _valor(p, "fecha_creacion", None)
        fecha_str = fecha.strftime("%d/%m/%Y") if fecha else "—"
        tabla_data.append([
            str(_valor(p, "id")), str(_valor(p, "donante_nombre")),
            str(_valor(p, "fundacion_nombre")), monto_str, fecha_str,
            str(_valor(p, "estado_pago", "Recibida")).capitalize()
        ])
    if len(tabla_data) == 1:
        tabla_data.append(["Sin pagos registrados.", "", "", "", "", ""])
    elementos.append(_tabla_estilizada(
        tabla_data, [1.5 * cm, 3.5 * cm, 3.5 * cm, 3 * cm, 2.5 * cm, 2.5 * cm]
    ))
    elementos.append(Spacer(1, 10))
    elementos.append(_barra_resumen(
        f"Total de pagos: {len(pagos)}", f"Total recaudado: ${total:,.0f} COP"
    ))


# =========================
# ORQUESTADOR PRINCIPAL (NUEVO)
# =========================

def generar_reporte_multi_seccion(secciones, datos):
    """
    Genera un PDF con una o varias secciones, cada una en su propia
    tabla, separadas por salto de página cuando hay más de una.

    secciones: lista de claves entre 'donantes', 'fundaciones',
    'donaciones', 'pagos', 'pendientes' (o esas 5 si se pide 'todos').

    datos: dict con las listas ya obtenidas de AdminManager, con claves
    'donantes', 'fundaciones', 'donaciones', 'pagos', 'pendientes'.
    Solo se usan las que correspondan a las secciones pedidas.
    """
    estilos = _estilos()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )

    if len(secciones) == 1:
        titulo_pdf = f"Reporte de {ETIQUETAS_SECCION.get(secciones[0], secciones[0].capitalize())}"
    else:
        titulo_pdf = "Reporte Ejecutivo General"

    elementos = [_bloque_encabezado(titulo_pdf, estilos), Spacer(1, 16)]

    constructores = {
        "donantes": lambda e: _seccion_donantes(e, estilos, datos.get("donantes", [])),
        "fundaciones": lambda e: _seccion_fundaciones(e, estilos, datos.get("fundaciones", [])),
        "donaciones": lambda e: _seccion_donaciones(e, estilos, datos.get("donaciones", [])),
        "pagos": lambda e: _seccion_pagos(e, estilos, datos.get("pagos", [])),
        "pendientes": lambda e: _seccion_fundaciones(
            e, estilos, datos.get("pendientes", []), titulo="Fundaciones Pendientes de Aprobación"
        ),
    }

    for i, seccion in enumerate(secciones):
        constructor = constructores.get(seccion)
        if not constructor:
            continue
        if i > 0:
            elementos.append(PageBreak())
            elementos.append(_bloque_encabezado(
                f"Reporte de {ETIQUETAS_SECCION.get(seccion, seccion.capitalize())}", estilos
            ))
            elementos.append(Spacer(1, 16))
        constructor(elementos)

    doc.build(elementos)
    buffer.seek(0)
    return buffer


# =========================
# FUNCIÓN ANTERIOR (SE MANTIENE INTACTA, sigue funcionando igual
# para no romper la ruta de descarga que ya está probada y funciona)
# =========================

def generar_reporte_pdf(donaciones, filtros=None):
    """
    Genera el PDF del reporte ejecutivo (solo Donaciones) en memoria y
    devuelve un objeto BytesIO listo para enviarse con send_file() o
    adjuntarse a un correo. Se mantiene para compatibilidad con el
    flujo ya probado; el nuevo selector de secciones usa
    generar_reporte_multi_seccion() en su lugar.
    """
    filtros = filtros or {}
    estilos = _estilos()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )

    elementos = [_bloque_encabezado("Reporte Ejecutivo de Donaciones", estilos), Spacer(1, 16)]

    elementos.append(Paragraph("Filtros aplicados", estilos["seccion"]))
    filtros_data = [
        ["Categoría:", filtros.get("categoria") or "Todas",
         "Estado:", filtros.get("estado") or "Todos"],
        ["Donante:", filtros.get("donante") or "—",
         "Fundación:", filtros.get("fundacion") or "—"],
    ]
    filtros_table = Table(filtros_data, colWidths=[3 * cm, 5.5 * cm, 3 * cm, 5.5 * cm])
    filtros_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(filtros_table)
    elementos.append(Spacer(1, 10))

    _seccion_donaciones(elementos, estilos, donaciones)

    doc.build(elementos)
    buffer.seek(0)
    return buffer


def filtrar_donaciones(donaciones, categoria=None, estado=None, donante=None, fundacion=None):
    """
    Filtra la lista de donaciones en memoria (no en SQL) según los
    parámetros opcionales. Pensado para listas ya pequeñas (decenas/
    cientos de filas), coherente con el tamaño esperado del proyecto.
    """
    resultado = []
    for d in donaciones:
        nombre_donante = _valor(d, "donante_nombre", "")
        nombre_fundacion = _valor(d, "fundacion_nombre", "")
        estado_actual = _valor(d, "estado_donacion", "")

        if estado and estado.lower() not in ["todos", ""] and estado_actual.lower() != estado.lower():
            continue
        if donante and donante.lower() not in nombre_donante.lower():
            continue
        if fundacion and fundacion.lower() not in nombre_fundacion.lower():
            continue

        resultado.append(d)

    return resultado