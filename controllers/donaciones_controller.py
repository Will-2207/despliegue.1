from flask import render_template, request, redirect, url_for, flash, session, current_app
from controllers import donaciones_bp
from decorators import login_required
from services.donacion_service import DonacionService
import stripe


# =========================
# PANEL DONANTE
# =========================
@donaciones_bp.route('/panel-donante', methods=['GET'])
@login_required
def inicio_donante():
    usuario_id = session.get('usuario_id')

    try:
        donante = DonacionService.obtener_donante_por_id(usuario_id)
        necesidades = DonacionService.obtener_necesidades_activas()
    except Exception as e:
        print(f"Error cargando panel donante: {e}")
        donante = None
        necesidades = []
        flash("No fue posible cargar el panel en este momento.", "danger")

    if not donante:
        donante = {'foto_perfil': 'default.png', 'nombre': 'Donante'}

    return render_template(
        'donante.html',
        donante=donante,
        necesidades=necesidades
    )


# =========================
# HISTORIAL DONANTE
# =========================
@donaciones_bp.route('/mis-donaciones', methods=['GET'])
@login_required
def historial_donante():
    usuario_id = session.get('usuario_id')

    try:
        donaciones = DonacionService.obtener_donaciones_usuario(usuario_id)
    except Exception as e:
        print(f"Error cargando historial de donaciones: {e}")
        donaciones = []
        flash("No fue posible cargar tus donaciones.", "danger")

    return render_template(
        'donante/historial.html',
        donaciones=donaciones
    )


# =========================
# REGISTRAR DONACION
# =========================
@donaciones_bp.route('/donar/<int:necesidad_id>', methods=['POST'])
@login_required
def registrar_donacion(necesidad_id):
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return redirect(url_for('auth.login'))

    cantidad = request.form.get('cantidad', 0)
    es_monetario = request.form.get('tipo') == 'monetario'
    detalles = request.form.to_dict()

    try:
        if es_monetario:
            session['donacion_pendiente'] = {
                'necesidad_id': necesidad_id,
                'monto': cantidad
            }
            return redirect(url_for('donaciones.pagar_stripe', necesidad_id=necesidad_id))

        exito, mensaje = DonacionService.registrar_donacion_fisica(
            necesidad_id=necesidad_id,
            donante_id=usuario_id,
            cantidad=cantidad,
            detalles=detalles,
            articulo=request.form.get('nombre_producto')
        )

        flash(mensaje, 'success' if exito else 'danger')
    except Exception as e:
        print(f"Error controlador registrar_donacion: {e}")
        flash("Error inesperado al registrar donacion.", "danger")

    return redirect(url_for('donaciones.historial_donante'))


# =========================
# FUNDACION DONACIONES
# =========================
@donaciones_bp.route('/fundacion/donaciones', methods=['GET'])
@login_required
def gestionar_donaciones():
    fundacion_id = session.get('fundacion_id') or DonacionService.obtener_fundacion_id_por_usuario(
        session.get('usuario_id')
    )

    if not fundacion_id:
        return redirect(url_for('auth.login'))

    try:
        donaciones = DonacionService.obtener_donaciones_por_fundacion(fundacion_id)
        pendientes = DonacionService.contar_donaciones_pendientes(fundacion_id)
    except Exception as e:
        print(f"Error cargando donaciones de fundacion: {e}")
        donaciones = []
        pendientes = 0
        flash("No fue posible cargar las donaciones.", "danger")

    return render_template(
        'fundacion/donaciones.html',
        donaciones=donaciones,
        pendientes=pendientes
    )


# =========================
# ACTUALIZAR ESTADO
# =========================
@donaciones_bp.route('/donacion/estado/<int:donacion_id>', methods=['POST'])
@login_required
def actualizar_estado(donacion_id):
    nuevo_estado = request.form.get('estado')

    try:
        actualizado = DonacionService.cambiar_estado(donacion_id, nuevo_estado)
    except Exception as e:
        print(f"Error actualizando estado de donacion: {e}")
        actualizado = False

    if actualizado:
        flash('Estado actualizado correctamente', 'success')
    else:
        flash('Error al actualizar estado', 'danger')

    return redirect(url_for('donaciones.gestionar_donaciones'))


# =========================
# STRIPE CHECKOUT
# =========================
@donaciones_bp.route('/pagar-stripe/<int:necesidad_id>', methods=['GET', 'POST'])
@login_required
def pagar_stripe(necesidad_id):
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        donacion_pendiente = session.get('donacion_pendiente') or {}
        monto = donacion_pendiente.get('monto', 0)

        if int(float(monto)) <= 0:
            flash("El monto de la donacion no es valido.", "danger")
            return redirect(url_for('donaciones.inicio_donante'))

        success_url = url_for(
            'donaciones.pago_exitoso',
            necesidad_id=necesidad_id,
            _external=True
        ) + "?session_id={CHECKOUT_SESSION_ID}"

        session_stripe = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'cop',
                    'unit_amount': int(float(monto)) * 100,
                    'product_data': {
                        'name': 'Donacion Solidaria'
                    }
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=url_for('donaciones.historial_donante', _external=True),
        )

        return redirect(session_stripe.url)
    except Exception as e:
        print(f"Error Stripe: {e}")
        flash("Error en el pago.", "danger")
        return redirect(url_for('donaciones.historial_donante'))


# =========================
# PAGO EXITOSO
# =========================
@donaciones_bp.route('/pago-exitoso/<int:necesidad_id>')
@login_required
def pago_exitoso(necesidad_id):
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            flash("No se recibio confirmacion del pago.", "danger")
            return redirect(url_for('donaciones.historial_donante'))

        stripe_session = stripe.checkout.Session.retrieve(session_id)
        payment_intent = stripe.PaymentIntent.retrieve(stripe_session.payment_intent)
        charge = stripe.Charge.retrieve(payment_intent.latest_charge)

        stripe_data = {
            'charge_id': charge.id,
            'brand': charge.payment_method_details.card.brand,
            'last4': charge.payment_method_details.card.last4,
            'email': stripe_session.customer_details.email
        }

        monto = stripe_session.amount_total / 100

        exito, mensaje = DonacionService.registrar_donacion_monetaria(
            usuario_id=session.get('usuario_id'),
            necesidad_id=necesidad_id,
            monto=float(monto),
            stripe_data=stripe_data
        )

        if exito:
            flash("Pago registrado correctamente", "success")
        else:
            flash(mensaje, "danger")
    except Exception as e:
        print(f"Error registrando pago exitoso: {e}")
        flash("El pago fue procesado, pero no fue posible registrar la donacion.", "danger")
    finally:
        session.pop('donacion_pendiente', None)

    return redirect(url_for('donaciones.historial_donante'))
