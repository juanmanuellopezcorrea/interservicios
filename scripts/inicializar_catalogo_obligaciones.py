"""Carga el catálogo de obligaciones si no existe. Ejecutar desde la raíz del proyecto:
   python scripts/inicializar_catalogo_obligaciones.py
"""
import os
import sys

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, basedir)

from app import app  # noqa: E402
from models import db, CatalogoObligaciones  # noqa: E402
from compliance_catalog_data import OBLIGACIONES  # noqa: E402


def main():
    with app.app_context():
        db.create_all()
        creados = 0
        for data in OBLIGACIONES:
            if CatalogoObligaciones.query.filter_by(codigo=data['codigo']).first():
                continue
            row = {k: v for k, v in data.items()}
            db.session.add(CatalogoObligaciones(**row))
            creados += 1
        db.session.commit()
        print(f'Catálogo: {creados} obligaciones nuevas (total definidas {len(OBLIGACIONES)}).')


if __name__ == '__main__':
    main()
