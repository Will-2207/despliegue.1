from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for, flash

db = SQLAlchemy()

# --- USUARIOS Y FUNDACIONES ---

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    direccion = db.Column(db.String(255)) # <--- ESTA ES LA LÍNEA NUEVA
    rol = db.Column(db.String(20), default='donante')
    stripe_customer_id = db.Column(db.String(100))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

class Fundacion(db.Model):
    __tablename__ = 'fundaciones'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nombre_fundacion = db.Column(db.String(200), nullable=False)
    nombre_persona_cargo = db.Column(db.String(200)) 
    telefono = db.Column(db.String(50))
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    foto_perfil = db.Column(db.String(255), default='default_logo.png')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    
    # --- AGREGA ESTOS NUEVOS CAMPOS ---
    nit = db.Column(db.String(50)) 
    
    # Relación para acceder al email del usuario fácilmente
    usuario = db.relationship('Usuario', backref='fundacion', lazy=True)
# --- NECESIDADES ---

class Necesidad(db.Model):
    __tablename__ = 'necesidades'
    id = db.Column(db.Integer, primary_key=True)
    fundacion_id = db.Column(db.Integer, db.ForeignKey('fundaciones.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    
    # Campos dinámicos para tu lógica nueva
    cantidad_requerida = db.Column(db.Integer, default=1)
    cantidad_comprometida = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(50)) # 'monetaria', 'alimentos', 'ropa', 'otros'
    detalles_json = db.Column(db.Text)   # JSON para guardar tallas, colores, etc.
    
    estado = db.Column(db.String(20), default='activa')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

# --- DONACIONES (ESTRUCTURA DE AUDITORÍA) ---

# --- DONACIONES (ESTRUCTURA DE AUDITORÍA) ---

class DonacionFisica(db.Model):
    __tablename__ = 'donaciones_fisicas'
    id = db.Column(db.Integer, primary_key=True)
    necesidad_id = db.Column(db.Integer, db.ForeignKey('necesidades.id'))
    donante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fundacion_id = db.Column(db.Integer, db.ForeignKey('fundaciones.id'))
    articulo = db.Column(db.String(200))
    cantidad_comprometida = db.Column(db.Integer)
    estado = db.Column(db.String(20), default='pendiente') # Agregué esta columna necesaria
    detalles_json = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'articulo': self.articulo,
            'cantidad': self.cantidad_comprometida,
            'estado': self.estado,
            'fecha': str(self.created_at)
        }

class DonacionMonetaria(db.Model):
    __tablename__ = 'donaciones_monetarias'
    id = db.Column(db.Integer, primary_key=True)
    necesidad_id = db.Column(db.Integer, db.ForeignKey('necesidades.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    monto = db.Column(db.Numeric(15, 2))
    stripe_charge_id = db.Column(db.String(255))
    card_brand = db.Column(db.String(50))
    card_last4 = db.Column(db.String(4))
    email_donante = db.Column(db.String(150))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'monto': float(self.monto),
            'brand': self.card_brand,
            'last4': self.card_last4,
            'fecha': str(self.created_at)
        }
# --- AUDITORÍA ---

class Auditoria(db.Model):
    __tablename__ = 'auditoria'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    accion = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    
class TicketSoporte(db.Model):
    __tablename__ = 'tickets_soporte'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    email = db.Column(db.String(100))
    mensaje = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())    
    