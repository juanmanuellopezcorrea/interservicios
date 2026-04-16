"""
Añade a la tabla trabajadores las columnas: email, password_hash, rol, activo.
Ejecutar una vez: python scripts/migrar_trabajadores_roles.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app
from app import db
from sqlalchemy import text

def migrar():
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            for col, sql in [
                ('email', 'ALTER TABLE trabajadores ADD COLUMN email VARCHAR(200)'),
                ('password_hash', 'ALTER TABLE trabajadores ADD COLUMN password_hash VARCHAR(255)'),
                ('rol', "ALTER TABLE trabajadores ADD COLUMN rol VARCHAR(20) DEFAULT 'TRABAJADOR'"),
                ('activo', 'ALTER TABLE trabajadores ADD COLUMN activo INTEGER DEFAULT 1'),
            ]:
                try:
                    conn.execute(text(sql))
                    print(f"  Columna '{col}' añadida.")
                except Exception as e:
                    if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                        print(f"  Columna '{col}' ya existe, omitiendo.")
                    else:
                        trans.rollback()
                        raise
            try:
                conn.execute(text("UPDATE trabajadores SET rol = 'TRABAJADOR' WHERE rol IS NULL"))
                conn.execute(text("UPDATE trabajadores SET activo = 1 WHERE activo IS NULL"))
            except Exception:
                pass
            trans.commit()
            print("Migración completada.")
        except Exception as e:
            trans.rollback()
            print("Error:", e)
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    migrar()
