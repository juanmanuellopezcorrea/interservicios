-- Script para crear usuario administrador inicial
-- Ejecutar en Supabase SQL Editor

-- Inserta el usuario admin con contraseña hasheada (bcrypt)
-- Usuario: admin
-- Contraseña: admin123 (hasheada como: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oeAx7eXHqUjy)

INSERT INTO usuarios (nombre, username, password_hash, rol) 
VALUES (
    'Administrador del Sistema',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oeAx7eXHqUjy',
    'ADMIN'
) ON CONFLICT (username) DO NOTHING;

-- Opcional: Insertar algunos trabajadores de ejemplo
INSERT INTO trabajadores (nombre, coste_hora, email, rol) 
VALUES 
    ('Juan González', 25.00, 'juan@interservicios.es', 'TRABAJADOR'),
    ('María López', 30.00, 'maria@interservicios.es', 'TRABAJADOR'),
    ('Carlos Martínez', 28.00, 'carlos@interservicios.es', 'TRABAJADOR')
ON CONFLICT DO NOTHING;

-- Opcional: Insertar algunos clientes de ejemplo
INSERT INTO clientes (nombre, cuota_mensual, modalidad_cuota, email, cif) 
VALUES 
    ('Empresa ABC SL', 500.00, 'PLUS', 'contacto@empresaabc.es', 'ESA12345678'),
    ('Distribuidora XYZ', 750.00, 'PREMIUM', 'info@distribuidora.es', 'ESB98765432'),
    ('Consultora 123', 300.00, 'BASICO', 'admin@consultora.es', 'ESC55555555')
ON CONFLICT DO NOTHING;

-- Opcional: Insertar algunas tareas
INSERT INTO tareas (nombre, tipo_tarea, incluida_contrato, precio_hora, incluida_cuota_basica) 
VALUES 
    ('Asesoramiento fiscal', 'CLIENTE', TRUE, 50.00, TRUE),
    ('Gestión laboral', 'CLIENTE', TRUE, 45.00, TRUE),
    ('Contabilidad', 'CLIENTE', TRUE, 60.00, FALSE),
    ('Revisión de documentos', 'INTERNA', FALSE, 35.00, FALSE)
ON CONFLICT DO NOTHING;

SELECT 'Usuario admin creado correctamente. Credenciales: admin / admin123' as mensaje;
