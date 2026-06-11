from flask import Flask, render_template, session, redirect, url_for
from database import get_db_connection
from controllers import auth_bp, donaciones_bp, fundacion_bp
import os
from dotenv import load_dotenv
import stripe

load_dotenv()

app = Flask(__name__)

# Configuración de seguridad
app.secret_key = os.getenv('SECRET_KEY', 'una_clave_muy_segura_y_larga_12345')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Registro de Blueprints (Controladores)
app.register_blueprint(auth_bp)
app.register_blueprint(donaciones_bp)
app.register_blueprint(fundacion_bp)

# Validación de variables de entorno
required_env = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'STRIPE_SECRET_KEY', 'MONGO_URI']
for var in required_env:
    if not os.getenv(var):
        print(f"¡ADVERTENCIA: La variable {var} no está configurada!")

# Manejador global de errores
@app.errorhandler(Exception)
def manejar_error(e):
    return render_template('error.html', mensaje_error="Ocurrió un problema técnico."), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)