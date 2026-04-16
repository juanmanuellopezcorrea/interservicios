"""
Entry point para Vercel serverless.
Importa la app Flask y la expone como handler WSGI.
"""
import sys
import os

# Agregar el directorio raiz al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, init_db

# Inicializar la base de datos en el primer request (solo crea tablas si no existen)
# En produccion, las tablas ya deben existir via migracion SQL
try:
    init_db()
except Exception as e:
    print(f"Warning: No se pudo inicializar DB: {e}")

# Handler para Vercel
handler = app
