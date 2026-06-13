from flask import Flask, render_template, session, redirect, url_for
from database import get_db_connection
from controllers import auth_bp, donaciones_bp, fundacion_bp
from controllers import auth_bp, donaciones_bp, fundacion_bp, admin_bp
from models import db  # <--- IMPORTANTE: Importar db
import os
from dotenv import load_dotenv
import stripe

load_dotenv()

app = Flask(__name__)

# Configuración de SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy con la app
db.init_app(app)

# Configuración de seguridad
app.secret_key = os.getenv('SECRET_KEY', 'una_clave_muy_segura_y_larga_12345')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Registro de Blueprints (Controladores)
app.register_blueprint(auth_bp)
app.register_blueprint(donaciones_bp)
app.register_blueprint(fundacion_bp)
app.register_blueprint(admin_bp)

# Validación de variables de entorno
required_env = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'STRIPE_SECRET_KEY', 'MONGO_URI', 'DATABASE_URL']
for var in required_env:
    if not os.getenv(var):
        print(f"¡ADVERTENCIA: La variable {var} no está configurada!")

# Crear las tablas al iniciar la aplicación (solo una vez)
with app.app_context():
    db.create_all()
        
@app.route('/debug-hash')
def debug_hash():
    from werkzeug.security import generate_password_hash
    return generate_password_hash('admin123')        

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)