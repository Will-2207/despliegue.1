from functools import wraps

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from services.auth_service import AuthService


auth_bp = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def redirect_user(rol):
    if rol == 'admin':
        return redirect(url_for('admin.dashboard'))
    if rol == 'fundacion':
        if not AuthService.fundacion_activa(session.get('usuario_id')):
            session.clear()
            flash("Tu fundacion aun no esta aprobada para ingresar.", "warning")
            return redirect(url_for('auth.login'))
        return redirect(url_for('fundacion.dashboard_fundacion'))
    return redirect(url_for('donaciones.inicio_donante'))


@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect_user(session.get('rol'))

    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('pass')

        exito, mensaje, usuario = AuthService.autenticar_usuario(email, password)

        if exito:
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre
            session['usuario_email'] = usuario.email
            session['rol'] = usuario.rol
            return redirect_user(usuario.rol)

        error = mensaje

    return render_template('login.html', error=error)


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        exito, mensaje = AuthService.registrar_usuario(request.form)
        flash(mensaje, 'success' if exito else 'danger')

        if exito:
            return redirect(url_for('auth.login'))

        return render_template('registro.html')

    return render_template('registro.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesion exitosamente.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/editar-perfil', methods=['POST'])
@login_required
def editar_perfil():
    exito, mensaje, nombre_sesion = AuthService.actualizar_perfil_fundacion(
        session.get('usuario_id'),
        request.form,
        request.files,
        current_app.root_path
    )

    flash(mensaje, 'success' if exito else 'danger')

    if exito and nombre_sesion:
        session['usuario_nombre'] = nombre_sesion

    return redirect(url_for('fundacion.dashboard_fundacion'))
