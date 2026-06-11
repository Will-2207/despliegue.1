from flask import Blueprint

# Definimos los Blueprints
auth_bp = Blueprint('auth_bp', __name__)
donaciones_bp = Blueprint('donaciones_bp', __name__)
fundacion_bp = Blueprint('fundacion_bp', __name__)
admin_bp = Blueprint('admin_bp', __name__)
# IMPORTANTE: Para que el IDE y Flask se lleven bien, 
# a veces ayuda importar los controladores aquí (al final del archivo):
from controllers import auth_controller, donaciones_controller, fundacion_controller,admin_controller