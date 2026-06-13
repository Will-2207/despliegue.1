from flask import render_template, request, redirect, url_for, flash, session
from . import auth_bp
from auth import AuthManager # Ajusta el import si tu archivo se llama distinto

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    # Si ya está logueado, redirigir según su rol
    if 'usuario_id' in session: 
        if session.get('rol') == 'admin':
            # CORRECCIÓN: Redirigir al panel de administrador real
            return redirect(url_for('admin_bp.dashboard'))
        return redirect(url_for('donaciones_bp.donante'))
        
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('pass')
        
        user = AuthManager.verificar_login(email, password)
        if user:
            # CORRECCIÓN CRÍTICA: Usar sintaxis de objeto (user.id) y no diccionario (user['id'])
            session['usuario_id'] = user.id
            session['usuario_nombre'] = user.nombre
            session['rol'] = user.rol
            
            # Redirección según rol corregida
            if user.rol == 'admin':
                return redirect(url_for('admin_bp.dashboard'))
            
            return redirect(url_for('donaciones_bp.donante'))
            
        # Mensaje ajustado para que cubra contraseñas malas o falta de aprobación
        error = "Credenciales incorrectas o cuenta pendiente de aprobación."
        
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

            # Llamamos al AuthManager que ya está en SQLAlchemy
            if AuthManager.registrar_usuario(nombre, email, password, direccion, telefono, tipo, datos_fundacion):
                flash('Registro exitoso, ahora puedes iniciar sesión.', 'success')
                return redirect(url_for('auth_bp.login'))
            error = "El correo ya está registrado o faltan datos."
        except Exception as e:
            error = f"Error: {str(e)}"
            
    return render_template('registro.html', error=error)

@auth_bp.route('/logout')
def logout():
    # Limpiamos la sesión completamente
    session.clear()
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for('auth_bp.login'))