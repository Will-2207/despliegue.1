from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for, flash

db = SQLAlchemy()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Asumiendo que guardas el rol en la sesión al loguearte
        if session.get('rol') != 'admin':
            flash("Acceso restringido: Solo para administradores.", "danger")
            return redirect(url_for('donaciones_bp.donante'))
        return f(*args, **kwargs)
    return decorated_function

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    rol = db.Column(db.String(20), default='donante') # Nuevo campo para control de acceso
    stripe_customer_id = db.Column(db.String(100))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relación con Fundación
    fundacion = db.relationship('Fundacion', backref='usuario', uselist=False)

class Fundacion(db.Model):
    __tablename__ = 'fundaciones'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nit = db.Column(db.String(50), unique=True, nullable=False)
    nombre_fundacion = db.Column(db.String(200), nullable=False)
    nombre_persona_cargo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    # Corregido: el nombre debe ser 'es_verificado' para que coincida con tu BD
    es_verificado = db.Column(db.Boolean, default=False) 
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

class Necesidad(db.Model):
    __tablename__ = 'necesidades'
    id = db.Column(db.Integer, primary_key=True)
    fundacion_id = db.Column(db.Integer, db.ForeignKey('fundaciones.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    monto_objetivo = db.Column(db.Numeric(15, 2), nullable=False)
    estado = db.Column(db.String(20), default='activa')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

class Donacion(db.Model):
    __tablename__ = 'donaciones'
    id = db.Column(db.Integer, primary_key=True)
    donante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    necesidad_id = db.Column(db.Integer, db.ForeignKey('necesidades.id'), nullable=False) # Trazabilidad
    monto = db.Column(db.Numeric(15, 2), nullable=False)
    token_uuid = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)