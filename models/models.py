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
    direccion = db.Column(db.String(255))
    rol = db.Column(db.String(20), default='donante')
    stripe_customer_id = db.Column(db.String(100))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    foto_perfil = db.Column(db.String(255), nullable=True)
    
    # ── AÑADE ESTA LÍNEA AQUÍ ──
    telefono = db.Column(db.String(20), nullable=True)

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
    
    cantidad_requerida = db.Column(db.Integer, default=1)
    cantidad_comprometida = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(50)) # 'monetaria', 'alimentos', 'ropa', 'otros'
    detalles_json = db.Column(db.Text)   # JSON para guardar tallas, colores, etc.
    
    estado = db.Column(db.String(20), default='activa')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # ── LA ÚNICA ADICIÓN AQUÍ: Relación limpia para no romper nada ──
    fundacion = db.relationship('Fundacion', backref='necesidades_asociadas', lazy=True)

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

    # ── NUEVO: fecha en que la donación fue marcada como 'recibida',
    # ya sea automáticamente (al cumplirse la meta de la necesidad) o
    # manualmente. Queda NULL mientras está pendiente.
    fecha_gestion = db.Column(db.TIMESTAMP, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'articulo': self.articulo,
            'cantidad': self.cantidad_comprometida,
            'estado': self.estado,
            'fecha': str(self.created_at),
            'fecha_gestion': str(self.fecha_gestion) if self.fecha_gestion else None
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

    # ── NUEVO: estado de la donación monetaria. Por defecto 'recibida'
    # porque si esta fila existe, es porque Stripe ya confirmó el pago.
    # Valores esperados: 'recibida' (default) o 'gestionada'.
    estado = db.Column(db.String(20), default='recibida')

    # ── NUEVO: relación ORM hacia Necesidad. No requiere migración porque
    # necesidad_id ya existía como columna; esto solo agrega el acceso
    # cómodo donacion_monetaria.necesidad en Python ──
    necesidad = db.relationship('Necesidad', backref='donaciones_monetarias_asociadas', lazy=True)

    # ── NUEVO: fecha de gestión, por consistencia con DonacionFisica.
    # En monetarias siempre coincide con created_at, porque el pago de
    # Stripe ya confirma la donación al instante (nace en 'recibida').
    fecha_gestion = db.Column(db.TIMESTAMP, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'monto': float(self.monto),
            'brand': self.card_brand,
            'last4': self.card_last4,
            'estado': self.estado,
            'fecha': str(self.created_at),
            'fecha_gestion': str(self.fecha_gestion) if self.fecha_gestion else None
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