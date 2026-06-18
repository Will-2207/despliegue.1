from waitress import serve
from app import app

if __name__ == '__main__':
    print("Servidor corriendo en http://localhost:5001")
    serve(app, host='0.0.0.0', port=5001)