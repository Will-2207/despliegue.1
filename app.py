import os
import stripe
from flask import Flask
from dotenv import load_dotenv
from flask_migrate import Migrate
from pymongo import MongoClient
from models.models import db

# 1. Cargar variables de entorno
load_dotenv()

# 2. Inicializar App
app = Flask(__name__)

# Configuración de Seguridad
app.secret_key = os.getenv('SECRET_KEY', 'una_clave_muy_segura_y_larga_12345')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# ── FIX: registramos la clave también en app.config, porque ──
# donaciones_controller.py la lee con current_app.config['STRIPE_SECRET_KEY']
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')

# Configuración Postgres (SQLAlchemy)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración Mongo (PyMongo)
mongo_uri = os.getenv('MONGO_URI')
if mongo_uri:
    try:
        app.mongo_client = MongoClient(mongo_uri)
        app.db_mongo = app.mongo_client.get_default_database()
    except Exception as e:
        app.logger.error(f"Error conectando a MongoDB: {e}")
        app.db_mongo = None
else:
    app.db_mongo = None

# Inicialización de extensiones
db.init_app(app)
migrate = Migrate(app, db)

# Crear tablas automáticamente
with app.app_context():
    db.create_all()

# 3. Importar y Registrar Controladores (Blueprints)
from controllers.auth_controller import auth_bp
from controllers.donaciones_controller import donaciones_bp
from controllers.fundacion_controller import fundacion_bp
from controllers.admin_controller import admin_bp

app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(donaciones_bp, url_prefix='/donaciones')
app.register_blueprint(fundacion_bp, url_prefix='/fundacion')
app.register_blueprint(admin_bp, url_prefix='/admin')

# 4. Health Check para Render
@app.route('/health')
def health_check():
    return {"status": "ok", "message": "Red Solidaria online"}, 200

if __name__ == '__main__':
    # Usar el puerto 5001 para local, Render usará la variable de entorno $PORT
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)