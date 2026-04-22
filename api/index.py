import os
import sys

# Añadir el directorio raíz al path para que pueda importar app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel requiere que la aplicación WSGI se llame 'app' o 'application'
application = app

if __name__ == "__main__":
    app.run()
