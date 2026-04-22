import os
import sys

# Configurar el path antes de cualquier import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar la aplicacion Flask
from app import app

# Vercel requiere que la aplicacion WSGI se llame 'app' o 'application'
application = app

# Handler para Vercel serverless functions
def handler(request):
    return app(request.environ, request.start_response)
