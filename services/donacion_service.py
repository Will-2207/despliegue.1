import json
from decimal import Decimal
from datetime import datetime

from models.models import db, DonacionFisica, DonacionMonetaria, Fundacion, Usuario, Necesidad
from email_service import EmailService
from email_templates import (
    correo_donante_fisica,
    correo_fundacion_fisica,
    correo_donante_monetaria,
    correo_fundacion_monetaria,
)


class _DonacionVista:
    """
    Objeto liviano que unifica DonacionFisica y DonacionMonetaria con los
    mismos nombres de atributo que donante.html ya espera en la tabla
    de 'Mi Trazabilidad y Aportes' (d.tipo, d.articulo, d.nombre_categoria,
    d.cantidad, d.estado, d.created_at, d.fecha_gestion, d.stripe_charge_id,
    d.foto_existe, d.fotos). No se guarda en base de datos, solo vive en
    memoria para renderizar la tabla.
    """
    def __init__(self, tipo, articulo, descripcion, nombre_categoria, cantidad,
                 estado, created_at, fecha_gestion, stripe_charge_id, foto_existe, fotos):
        self.tipo = tipo
        self.articulo = articulo
        self.descripcion = descripcion
        self.nombre_categoria = nombre_categoria
        self.cantidad = cantidad
        self.estado = estado
        self.created_at = created_at
        self.fecha_gestion = fecha_gestion
        self.stripe_charge_id = stripe_charge_id
        self.foto_existe = foto_existe
        self.fotos = fotos


class DonacionService:
    """
    Capa de negocio para donaciones.
    Los controladores no deben consultar SQLAlchemy directamente.
    """

    # =========================
    # USUARIO
    # =========================
    @staticmethod
    def obtener_donante_por_id(usuario_id):
        try:
            user = Usuario.query.filter_by(id=usuario_id).first()
        except Exception as e:
            print(f"Error obteniendo donante: {e}")
            return None

        if not user:
            return None

        # ── CORRECCIÓN INTEGRAL AQUÍ: Mapeamos los campos reales recién agregados ──
        return {
            "id": user.id,
            "nombre": user.nombre,
            "email": user.email,
            "foto_perfil": user.foto_perfil if user.foto_perfil else "default.png",
            "telefono": user.telefono if user.telefono else "",
            "direccion": user.direccion if user.direccion else ""
        }

    @staticmethod
    def obtener_fundacion_id_por_usuario(usuario_id):
        try:
            fundacion = Fundacion.query.filter_by(usuario_id=usuario_id).first()
            return fundacion.id if fundacion else None
        except Exception as e:
            print(f"Error obteniendo fundacion por usuario: {e}")
            return None

    # =========================
    # NECESIDADES
    # =========================
    @staticmethod
    def obtener_necesidades_activas():
        try:
            # Filtramos que el estado sea estrictamente 'activa'
            lista_necesidades = (
                Necesidad.query
                .filter_by(estado="activa")
                .order_by(Necesidad.created_at.desc())
                .all()
            )
            
            # Procesamos dinámicamente el JSON de cada necesidad de forma segura
            for necesidad in lista_necesidades:
                necesidad.detalles_dict = {}
                if necesidad.detalles_json:
                    try:
                        necesidad.detalles_dict = json.loads(necesidad.detalles_json)
                    except Exception as json_err:
                        print(f"Error parseando detalles_json para necesidad {necesidad.id}: {json_err}")
                        necesidad.detalles_dict = {}
            
            return lista_necesidades
        except Exception as e:
            print(f"Error obteniendo necesidades activas: {e}")
            return []

    # =========================
    # DONACIONES (LECTURA)
    # =========================
    # FILTRO MULTICRITERIO (Mi Trazabilidad y Aportes)
    # =========================
    @staticmethod
    def obtener_donaciones_filtradas(usuario_id, q=None, categoria=None, est=None):
        """
        Devuelve la lista unificada (física + monetaria) del donante,
        aplicando los filtros del formulario de donante.html.

        Los filtros se combinan con OR: si se pasa más de uno, basta con
        que la donación cumpla cualquiera de ellos para aparecer.

        categoria puede ser: 'alimentos', 'ropa', 'otros' (categorías
        reales de Necesidad) o 'Causa Social (Monetaria)' (trae monetarias).
        est aplica a ambos tipos: las físicas usan su columna estado real,
        las monetarias usan su nuevo estado ('recibida' / 'gestionada').
        """
        try:
            filtros_activos = bool(q or categoria or est)

            # ── Donaciones físicas, con JOIN a Necesidad para poder
            # filtrar por la categoría real (alimentos/ropa/otros) ──
            query_fisicas = (
                db.session.query(DonacionFisica, Necesidad)
                .outerjoin(Necesidad, DonacionFisica.necesidad_id == Necesidad.id)
                .filter(DonacionFisica.donante_id == usuario_id)
            )

            fisicas_resultado = []
            for donacion, necesidad in query_fisicas.all():
                cat_real = necesidad.categoria if necesidad else None
                cumple = not filtros_activos

                if q and donacion.articulo and q.lower() in donacion.articulo.lower():
                    cumple = True
                if categoria and categoria != "Causa Social (Monetaria)" and cat_real == categoria:
                    cumple = True
                if est and donacion.estado == est:
                    cumple = True

                if cumple:
                    fisicas_resultado.append(DonacionService._wrap_fisica(donacion, cat_real))

            # ── Donaciones monetarias (no tienen JOIN de categoría propia,
            # su "categoría" siempre es Causa Social) ──
            query_monetarias = DonacionMonetaria.query.filter_by(usuario_id=usuario_id)

            monetarias_resultado = []
            for donacion in query_monetarias.all():
                cumple = not filtros_activos

                if categoria == "Causa Social (Monetaria)":
                    cumple = True
                if est and donacion.estado == est:
                    cumple = True
                # 'q' no aplica a monetarias porque no tienen un campo de
                # texto libre equivalente a 'articulo'

                if cumple:
                    monetarias_resultado.append(DonacionService._wrap_monetaria(donacion))

            todas = fisicas_resultado + monetarias_resultado
            todas.sort(key=lambda d: d.created_at or datetime.min, reverse=True)
            return todas
        except Exception as e:
            print(f"Error filtrando donaciones del donante: {e}")
            return []

    @staticmethod
    def _wrap_fisica(donacion, categoria_real):
        return _DonacionVista(
            tipo="fisica",
            articulo=donacion.articulo,
            descripcion=donacion.articulo,
            nombre_categoria=categoria_real or "General",
            cantidad=donacion.cantidad_comprometida,
            estado=donacion.estado,
            created_at=donacion.created_at,
            fecha_gestion=donacion.fecha_gestion,
            stripe_charge_id=None,
            foto_existe=False,
            fotos=None
        )

    @staticmethod
    def _wrap_monetaria(donacion):
        return _DonacionVista(
            tipo="monetario",
            articulo="Aporte Económico Causa",
            descripcion="Aporte Económico Causa",
            nombre_categoria="Causa Social (Monetaria)",
            cantidad=float(donacion.monto or 0),
            estado=donacion.estado,
            created_at=donacion.created_at,
            fecha_gestion=donacion.fecha_gestion,
            stripe_charge_id=donacion.stripe_charge_id,
            foto_existe=False,
            fotos=None
        )

    @staticmethod
    def obtener_donaciones_por_fundacion(fundacion_id):
        """
        Mantiene la firma original sin filtros para no romper a quien ya
        la llama (ej. /fundacion/donaciones). Internamente delega en la
        versión filtrable sin pasar ningún filtro.
        """
        return DonacionService.obtener_donaciones_filtradas_fundacion(fundacion_id)

    @staticmethod
    def obtener_donaciones_filtradas_fundacion(fundacion_id, q=None, donante=None, categoria=None, est=None):
        """
        Igual que obtener_donaciones_filtradas (panel donante), pero para
        el panel de fundación. Aplica los mismos 4 filtros que ya existen
        en el formulario de dashboard_fundacion.html: q (descripción),
        donante (nombre), categoria (alimentos/ropa/otros/Causa Social),
        est (pendiente/recibida). Se combinan con OR, igual que en el
        panel del donante, para mantener consistencia de comportamiento
        entre ambos paneles.
        """
        try:
            filtros_activos = bool(q or donante or categoria or est)

            fisicas = (
                db.session.query(DonacionFisica, Usuario, Necesidad)
                .join(Usuario, DonacionFisica.donante_id == Usuario.id)
                .outerjoin(Necesidad, DonacionFisica.necesidad_id == Necesidad.id)
                .filter(DonacionFisica.fundacion_id == fundacion_id)
                .all()
            )

            monetarias = (
                db.session.query(DonacionMonetaria, Usuario, Necesidad)
                .join(Usuario, DonacionMonetaria.usuario_id == Usuario.id)
                .join(Necesidad, DonacionMonetaria.necesidad_id == Necesidad.id)
                .filter(Necesidad.fundacion_id == fundacion_id)
                .all()
            )

            resultado = []

            for d, u, n in fisicas:
                cat_real = n.categoria if n else None
                cumple = not filtros_activos

                if q and d.articulo and q.lower() in d.articulo.lower():
                    cumple = True
                if donante and u and u.nombre and donante.lower() in u.nombre.lower():
                    cumple = True
                if categoria and categoria != "Causa Social (Monetaria)" and cat_real == categoria:
                    cumple = True
                if est and d.estado == est:
                    cumple = True

                if not cumple:
                    continue

                resultado.append({
                    "id": d.id, "tipo": "fisica", "nombre_categoria": cat_real or "Física",
                    "articulo": d.articulo, "cantidad": d.cantidad_comprometida,
                    "estado": d.estado, "created_at": d.created_at,
                    "fecha_gestion": d.fecha_gestion,
                    "nombre_donante": u.nombre if u else "Anónimo",
                    "correo": u.email if u and u.email else "Sin correo",
                    "telefono": u.telefono if u and u.telefono else "Sin teléfono",
                    "descripcion": d.articulo, "foto_existe": False,
                    "card_brand": None, "card_last4": None
                })

            for d, u, n in monetarias:
                cumple = not filtros_activos

                if categoria == "Causa Social (Monetaria)":
                    cumple = True
                if donante and u and u.nombre and donante.lower() in u.nombre.lower():
                    cumple = True
                if est and d.estado == est:
                    cumple = True
                # 'q' no aplica a monetarias, igual que en el panel del donante:
                # no tienen un campo de texto libre equivalente a 'articulo'.

                if not cumple:
                    continue

                resultado.append({
                    "id": d.id, "tipo": "monetario", "nombre_categoria": "Causa Social",
                    "articulo": n.titulo if n else "Causa Social",
                    "cantidad": float(d.monto), "estado": d.estado, "created_at": d.created_at,
                    "fecha_gestion": d.fecha_gestion,
                    "nombre_donante": u.nombre if u else "Anónimo",
                    "correo": d.email_donante or (u.email if u else "Sin correo"),
                    "telefono": u.telefono if u and u.telefono else "Sin teléfono",
                    "descripcion": n.titulo if n else "Donación monetaria", "foto_existe": False,
                    "card_brand": d.card_brand, "card_last4": d.card_last4
                })

            return sorted(resultado, key=lambda x: x['created_at'], reverse=True)
        except Exception as e:
            print(f"Error filtrando donaciones por fundacion: {e}")
            return []

    @staticmethod
    def contar_donaciones_pendientes(fundacion_id):
        try:
            return DonacionFisica.query.filter_by(
                fundacion_id=fundacion_id,
                estado="pendiente"
            ).count()
        except Exception as e:
            print(f"Error contando donaciones pendientes: {e}")
            return 0

    # =========================
    # DONACIONES (ESCRITURA)
    # =========================
    @staticmethod
    def registrar_donacion_fisica(
        necesidad_id,
        donante_id,
        cantidad,
        detalles=None,
        fundacion_id=None,
        articulo=None
    ):
        try:
            necesidad = (
                Necesidad.query
                .filter_by(id=necesidad_id, estado="activa")
                .with_for_update()
                .first()
            )

            if not necesidad:
                return False, "La necesidad no existe o ya no esta disponible."

            cantidad = int(cantidad or 0)
            if cantidad <= 0:
                return False, "La cantidad debe ser mayor a cero."

            nueva = DonacionFisica(
                necesidad_id=necesidad.id,
                donante_id=donante_id,
                fundacion_id=fundacion_id or necesidad.fundacion_id,
                articulo=articulo or necesidad.titulo,
                cantidad_comprometida=cantidad,
                detalles_json=json.dumps(detalles or {}),
                estado="pendiente"
            )

            necesidad.cantidad_comprometida = (necesidad.cantidad_comprometida or 0) + cantidad

            db.session.add(nueva)

            if necesidad.cantidad_comprometida >= necesidad.cantidad_requerida:
                necesidad.estado = "finalizada"
                # ── SINCRONIZACIÓN AUTOMÁTICA: al cumplirse la meta de la
                # necesidad, TODAS sus donaciones físicas (incluida la que
                # acabamos de crear, ya en sesión) pasan a 'recibida' sin
                # que la fundación tenga que aceptarlas una por una.
                # fecha_gestion se llena en este mismo instante porque es
                # justo cuando el sistema "completa" la donación. ──
                db.session.flush()  # asegura que 'nueva' ya tenga id asignado
                DonacionFisica.query.filter_by(necesidad_id=necesidad.id).update(
                    {"estado": "recibida", "fecha_gestion": datetime.utcnow()}
                )

            db.session.commit()

            # ── NOTIFICACIONES POR CORREO (no bloquean la transacción si fallan) ──
            try:
                DonacionService._notificar_donacion_fisica(
                    donante_id=donante_id,
                    necesidad=necesidad,
                    articulo=nueva.articulo,
                    cantidad=cantidad,
                    fecha=nueva.created_at
                )
            except Exception as email_err:
                print(f"Aviso: no se pudo enviar notificacion de correo (fisica): {email_err}")

            return True, "Donacion fisica registrada correctamente"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def registrar_donacion_monetaria(usuario_id, necesidad_id, monto, stripe_data):
        try:
            necesidad = (
                Necesidad.query
                .filter_by(id=necesidad_id)
                .with_for_update()
                .first()
            )

            if not necesidad:
                return False, "La necesidad no existe."

            monto_decimal = Decimal(str(monto or 0))
            if monto_decimal <= 0:
                return False, "El monto debe ser mayor a cero."

            nueva = DonacionMonetaria(
                usuario_id=usuario_id,
                necesidad_id=necesidad.id,
                monto=monto_decimal,
                stripe_charge_id=stripe_data.get("charge_id"),
                card_brand=stripe_data.get("brand"),
                card_last4=stripe_data.get("last4"),
                email_donante=stripe_data.get("email"),
                estado="recibida",
                fecha_gestion=datetime.utcnow()
            )

            necesidad.cantidad_comprometida = (necesidad.cantidad_comprometida or 0) + int(monto_decimal)
            if necesidad.cantidad_comprometida >= necesidad.cantidad_requerida:
                necesidad.estado = "finalizada"

            db.session.add(nueva)
            db.session.commit()

            # ── NOTIFICACIONES POR CORREO (no bloquean la transacción si fallan) ──
            try:
                DonacionService._notificar_donacion_monetaria(
                    usuario_id=usuario_id,
                    necesidad=necesidad,
                    monto=monto_decimal,
                    stripe_data=stripe_data,
                    fecha=nueva.created_at
                )
            except Exception as email_err:
                print(f"Aviso: no se pudo enviar notificacion de correo (monetaria): {email_err}")

            return True, "Donacion monetaria registrada correctamente"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    # =========================
    # ESTADOS
    # =========================
    @staticmethod
    def cambiar_estado(donacion_id, nuevo_estado):
        try:
            estados_validos = {"pendiente", "recibida", "rechazada", "cancelada"}
            if nuevo_estado not in estados_validos:
                return False

            donacion = DonacionFisica.query.get(donacion_id)
            if not donacion:
                return False

            donacion.estado = nuevo_estado
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error cambiando estado: {e}")
            return False

    # =========================
    # NOTIFICACIONES POR CORREO (BREVO)
    # =========================
    @staticmethod
    def _notificar_donacion_fisica(donante_id, necesidad, articulo, cantidad, fecha):
        """
        Envia el correo de confirmacion al donante y el aviso a la fundacion
        cuando se registra una donacion fisica. Cualquier fallo aqui se
        registra en consola pero NUNCA revierte la donacion ya guardada.
        """
        fecha_str = fecha.strftime('%d/%m/%Y %H:%M') if fecha else '-'

        donante = Usuario.query.get(donante_id)
        fundacion = Fundacion.query.get(necesidad.fundacion_id) if necesidad else None
        fundacion_usuario = fundacion.usuario if fundacion else None

        nombre_fundacion = fundacion.nombre_fundacion if fundacion else "Red Solidaria"

        # Correo al donante
        if donante and donante.email:
            html_donante = correo_donante_fisica(
                nombre_donante=donante.nombre,
                fundacion_nombre=nombre_fundacion,
                articulo=articulo,
                cantidad=cantidad,
                fecha=fecha_str
            )
            EmailService.enviar_notificacion(
                email_destino=donante.email,
                nombre_destino=donante.nombre,
                asunto="¡Tu donación física fue registrada! - Red Solidaria",
                html_content=html_donante
            )

        # Correo a la fundación
        if fundacion_usuario and fundacion_usuario.email:
            html_fundacion = correo_fundacion_fisica(
                nombre_fundacion=nombre_fundacion,
                donante_nombre=donante.nombre if donante else "Un donante",
                articulo=articulo,
                cantidad=cantidad,
                fecha=fecha_str
            )
            EmailService.enviar_notificacion(
                email_destino=fundacion_usuario.email,
                nombre_destino=nombre_fundacion,
                asunto="Nueva donación física recibida - Red Solidaria",
                html_content=html_fundacion
            )

    @staticmethod
    def _notificar_donacion_monetaria(usuario_id, necesidad, monto, stripe_data, fecha):
        """
        Envia el correo de confirmacion al donante y el aviso a la fundacion
        cuando se registra una donacion monetaria via Stripe.
        """
        fecha_str = fecha.strftime('%d/%m/%Y %H:%M') if fecha else '-'
        monto_str = "{:,.0f}".format(float(monto))

        donante = Usuario.query.get(usuario_id)
        fundacion = Fundacion.query.get(necesidad.fundacion_id) if necesidad else None
        fundacion_usuario = fundacion.usuario if fundacion else None

        nombre_fundacion = fundacion.nombre_fundacion if fundacion else "Red Solidaria"
        nombre_necesidad = necesidad.titulo if necesidad else "Causa Social"
        card_brand = stripe_data.get("brand")
        card_last4 = stripe_data.get("last4")

        # Correo al donante
        if donante and donante.email:
            html_donante = correo_donante_monetaria(
                nombre_donante=donante.nombre,
                fundacion_nombre=nombre_fundacion,
                nombre_necesidad=nombre_necesidad,
                monto=monto_str,
                card_brand=card_brand,
                card_last4=card_last4,
                fecha=fecha_str
            )
            EmailService.enviar_notificacion(
                email_destino=donante.email,
                nombre_destino=donante.nombre,
                asunto=f"¡Tu aporte para {nombre_fundacion} fue confirmado! - Red Solidaria",
                html_content=html_donante
            )

        # Correo a la fundación
        if fundacion_usuario and fundacion_usuario.email:
            html_fundacion = correo_fundacion_monetaria(
                nombre_fundacion=nombre_fundacion,
                donante_nombre=donante.nombre if donante else "Un donante",
                nombre_necesidad=nombre_necesidad,
                monto=monto_str,
                card_brand=card_brand,
                card_last4=card_last4,
                fecha=fecha_str
            )
            EmailService.enviar_notificacion(
                email_destino=fundacion_usuario.email,
                nombre_destino=nombre_fundacion,
                asunto="Nuevo aporte monetario recibido - Red Solidaria",
                html_content=html_fundacion
            )