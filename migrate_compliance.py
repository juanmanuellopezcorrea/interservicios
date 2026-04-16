"""
Añade columnas de compliance/onboarding a la tabla `clientes` (SQLite).
Ejecutar una vez: python migrate_compliance.py
Las tablas nuevas (catalogo_obligaciones, etc.) las crea db.create_all() al arrancar la app.
"""
import os
import sqlite3

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'servicios_profesionales.db').replace('\\', '/')

# (nombre_columna, SQL tipo SQLite con DEFAULT si aplica)
COLUMNAS = [
    ('activo', 'INTEGER NOT NULL DEFAULT 1'),
    ('cif', 'TEXT'),
    ('email', 'TEXT'),
    ('telefono', 'TEXT'),
    ('razon_social', 'TEXT'),
    ('nombre_comercial', 'TEXT'),
    ('direccion_fiscal', 'TEXT'),
    ('codigo_postal', 'TEXT'),
    ('municipio', 'TEXT'),
    ('provincia', 'TEXT'),
    ('pais', 'TEXT'),
    ('persona_contacto', 'TEXT'),
    ('cargo_contacto', 'TEXT'),
    ('telefono_contacto', 'TEXT'),
    ('email_contacto', 'TEXT'),
    ('persona_contacto_2', 'TEXT'),
    ('telefono_contacto_2', 'TEXT'),
    ('email_contacto_2', 'TEXT'),
    ('tipo_sociedad', 'TEXT'),
    ('fecha_constitucion', 'TEXT'),
    ('capital_social', 'REAL'),
    ('num_socios', 'INTEGER'),
    ('cnae_principal', 'TEXT'),
    ('cnae_descripcion', 'TEXT'),
    ('cnae_secundarios', 'TEXT'),
    ('descripcion_actividad', 'TEXT'),
    ('sector', 'TEXT'),
    ('tiene_empleados', 'INTEGER NOT NULL DEFAULT 0'),
    ('num_empleados_actual', 'INTEGER NOT NULL DEFAULT 0'),
    # Nuevas columnas requeridas por compliance_engine.py
    ('num_empleados', 'INTEGER NOT NULL DEFAULT 0'),
    ('prevision_contratacion', 'INTEGER NOT NULL DEFAULT 0'),
    ('prevision_num_empleados', 'INTEGER NOT NULL DEFAULT 0'),
    ('prevision_plazo_meses', 'INTEGER'),
    ('empleados_oficina', 'INTEGER NOT NULL DEFAULT 0'),
    ('empleados_teletrabajo', 'INTEGER NOT NULL DEFAULT 0'),
    ('empleados_obra', 'INTEGER NOT NULL DEFAULT 0'),
    ('empleados_vehiculos', 'INTEGER NOT NULL DEFAULT 0'),
    ('empleados_turnos', 'INTEGER NOT NULL DEFAULT 0'),
    ('empleados_nocturnos', 'INTEGER NOT NULL DEFAULT 0'),
    ('convenio_aplicable', 'TEXT'),
    ('convenio_codigo', 'TEXT'),
    ('facturacion_anual', 'TEXT'),
    ('facturacion_estimada', 'REAL'),
    ('opera_efectivo', 'TEXT'),
    ('sector_obligado_blanqueo', 'INTEGER NOT NULL DEFAULT 0'),
    ('volumen_efectivo_anual', 'REAL'),
    ('exporta', 'INTEGER NOT NULL DEFAULT 0'),
    ('paises_exportacion', 'TEXT'),
    ('tiene_local', 'INTEGER NOT NULL DEFAULT 0'),
    ('direccion_local', 'TEXT'),
    ('tipo_local', 'TEXT'),
    ('superficie_m2', 'REAL'),
    ('num_locales', 'INTEGER NOT NULL DEFAULT 0'),
    ('tiene_almacen', 'INTEGER NOT NULL DEFAULT 0'),
    ('almacena_quimicos', 'INTEGER NOT NULL DEFAULT 0'),
    ('tiene_maquinaria', 'INTEGER NOT NULL DEFAULT 0'),
    ('manipula_alimentos', 'INTEGER NOT NULL DEFAULT 0'),
    ('tiene_climatizacion', 'INTEGER NOT NULL DEFAULT 0'),
    ('potencia_climatizacion_kw', 'REAL'),
    ('potencia_climat_kw', 'REAL NOT NULL DEFAULT 0'),
    ('tiene_ascensor', 'INTEGER NOT NULL DEFAULT 0'),
    ('tiene_parking', 'INTEGER NOT NULL DEFAULT 0'),
    ('tiene_web', 'INTEGER NOT NULL DEFAULT 0'),
    ('url_web', 'TEXT'),
    ('tiene_rrss', 'INTEGER NOT NULL DEFAULT 0'),
    ('rrss_activas', 'TEXT'),
    ('tiene_ecommerce', 'INTEGER NOT NULL DEFAULT 0'),
    ('plataforma_ecommerce', 'TEXT'),
    ('trata_datos_personales', 'INTEGER NOT NULL DEFAULT 0'),
    ('trata_datos_especiales', 'INTEGER NOT NULL DEFAULT 0'),
    ('volumen_datos', 'TEXT'),
    ('trata_datos_contacto', 'INTEGER NOT NULL DEFAULT 0'),
    ('trata_datos_economicos', 'INTEGER NOT NULL DEFAULT 0'),
    ('trata_datos_salud', 'INTEGER NOT NULL DEFAULT 0'),
    ('trata_datos_menores', 'INTEGER NOT NULL DEFAULT 0'),
    ('trata_datos_biometricos', 'INTEGER NOT NULL DEFAULT 0'),
    ('trata_datos_judicial', 'INTEGER NOT NULL DEFAULT 0'),
    ('iban', 'TEXT'),
    ('titular_cuenta', 'TEXT'),
    ('banco', 'TEXT'),
    ('forma_pago', 'TEXT'),
    ('dia_facturacion', 'INTEGER'),
    ('dia_vencimiento', 'INTEGER'),
    ('descuento_aplicable', 'REAL NOT NULL DEFAULT 0'),
    ('observaciones_comerciales', 'TEXT'),
    ('onboarding_completado', 'INTEGER NOT NULL DEFAULT 0'),
    ('onboarding_fecha_inicio', 'TEXT'),
    ('onboarding_fecha_fin', 'TEXT'),
    ('onboarding_paso_actual', 'INTEGER NOT NULL DEFAULT 1'),
    ('onboarding_porcentaje', 'INTEGER NOT NULL DEFAULT 0'),
    ('ultimo_analisis_compliance', 'TEXT'),
    ('proximo_analisis_compliance', 'TEXT'),
    ('nivel_riesgo_compliance', 'TEXT'),
    ('compliance_porcentaje', 'INTEGER NOT NULL DEFAULT 0'),
]


def main():
    print('BD:', db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('PRAGMA table_info(clientes)')
    existentes = {row[1] for row in cur.fetchall()}
    n = 0
    for nombre, tipo in COLUMNAS:
        if nombre in existentes:
            continue
        sql = f'ALTER TABLE clientes ADD COLUMN {nombre} {tipo}'
        print(' +', sql)
        cur.execute(sql)
        n += 1
    conn.commit()
    conn.close()
    print(f'Listo. Columnas añadidas: {n}')


if __name__ == '__main__':
    main()
