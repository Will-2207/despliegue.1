from flask import render_template, request, redirect, url_for, flash, session
from . import auth_bp
from auth import AuthManager

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    # Si ya está logueado, redirigir al donante
    if 'usuario_id' in session: 
        return redirect(url_for('donaciones_bp.donante'))
        
    error = None
    if request.method == 'POST':
        user = AuthManager.verificar_login(request.form.get('email'), request.form.get('pass'))
        if user:
            # Guardamos los datos clave en la sesión
            session['usuario_id'] = user['id']
            session['usuario_nombre'] = user['nombre']
            session['rol'] = user['rol']  # <--- Integrado: clave para el control de acceso
            
            # Redirección según rol (opcional, pero recomendado)
            if user['rol'] == 'admin':
                return redirect(url_for('admin_bp.dashboard')) # O tu ruta de admin
            return redirect(url_for('donaciones_bp.donante'))
            
        error = "Credenciales incorrectas."
        
    return render_template('login.html', error=error)

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    error = None
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            password = request.form.get('pass')
            direccion = request.form.get('direccion')
            telefono = request.form.get('telefono')
            tipo = request.form.get('tipo_persona')
            
            datos_fundacion = None
            if tipo == 'juridica':
                datos_fundacion = {
                    'nit': request.form.get('nit'),
                    'nombre_fundacion': request.form.get('nombre_fundacion'),
                    'nombre_persona_cargo': nombre,
                    'descripcion': request.form.get('descripcion')
                }

            if AuthManager.registrar_usuario(nombre, email, password, direccion, telefono, tipo, datos_fundacion):
                flash('Registro exitoso, ahora puedes iniciar sesión.', 'success')
                return redirect(url_for('auth_bp.login'))
            error = "No fue posible registrar el usuario."
        except Exception as e:
            error = f"Error: {str(e)}"
            
    return render_template('registro.html', error=error)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for('auth_bp.login'))