#!/usr/bin/env python3
"""
Script para inicializar la aplicación en Vercel.
Se ejecuta después del build y antes de que los servidores empiecen.
"""

import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Solo inicializar si estamos en producción
if os.environ.get('VERCEL'):
    try:
        print("[init] Starting database initialization...")
        from app import app, db, init_db
        from models import Usuario
        
        with app.app_context():
            print("[init] Database URI:", app.config['SQLALCHEMY_DATABASE_URI'][:50] + "...")
            
            # Verificar que podemos conectar a la base de datos
            try:
                result = db.session.execute("SELECT 1")
                print("[init] ✓ Database connection successful")
            except Exception as e:
                print(f"[init] ✗ Database connection failed: {e}")
                sys.exit(1)
            
            # Crear usuario admin si no existe
            admin = Usuario.query.filter_by(username='admin').first()
            if not admin:
                try:
                    admin = Usuario(nombre='Administrador', username='admin', rol='ADMIN')
                    admin.set_password('admin')
                    db.session.add(admin)
                    db.session.commit()
                    print("[init] ✓ Admin user created (admin/admin)")
                except Exception as e:
                    print(f"[init] ✓ Admin user already exists or error: {e}")
                    db.session.rollback()
            else:
                print("[init] ✓ Admin user already exists")
                
        print("[init] Database initialization complete!")
        
    except Exception as e:
        print(f"[init] ✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
