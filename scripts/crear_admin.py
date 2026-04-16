"""
Crea el primer administrador (Trabajador con rol ADMIN) para login por email.
Ejecutar una vez después de migrar: python scripts/crear_admin.py

Por defecto: admin@empresa.com / Admin123!
Cambiar contraseña en producción.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app
from models import db, Trabajador

def crear_admin():
    with app.app_context():
        email = os.environ.get('ADMIN_EMAIL', 'admin@empresa.com')
        password = os.environ.get('ADMIN_PASSWORD', 'Admin123!')
        nombre = os.environ.get('ADMIN_NOMBRE', 'Administrador')

        admin = Trabajador.query.filter_by(email=email).first()
        if admin:
            print("Ya existe un trabajador con ese email. Para resetear contraseña, edítalo desde la app.")
            return

        admin = Trabajador(
            nombre=nombre,
            email=email,
            rol='ADMIN',
            coste_hora=0,
            activo=True,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print("Administrador creado correctamente.")
        print("  Email:", email)
        print("  Contraseña: (la indicada; por defecto Admin123!)")
        print("  Cambiar la contraseña en producción.")

if __name__ == '__main__':
    crear_admin()
