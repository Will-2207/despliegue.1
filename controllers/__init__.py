from flask import Blueprint

# 1. Definimos los Blueprints con nombres consistentes
# Asegúrate de usar estos mismos nombres en tus url_for('nombre_bp.ruta')
# Edita tu __init__.py y déjalo así:
auth_bp = Blueprint('auth', __name__)
donaciones_bp = Blueprint('donaciones', __name__)
fundacion_bp = Blueprint('fundacion', __name__)
admin_bp = Blueprint('admin', __name__)

# 2. Importamos los controladores al final para registrar las rutas
from . import auth_controller, donaciones_controller, fundacion_controller, admin_controller