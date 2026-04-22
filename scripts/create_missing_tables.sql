-- Create solicitud_presupuesto table if not exists
CREATE TABLE IF NOT EXISTS solicitud_presupuesto (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    obligacion_id INTEGER REFERENCES obligacion_cliente_legacy(id),
    catalogo_id INTEGER REFERENCES catalogo_obligaciones_legacy(id),
    estado VARCHAR(50) DEFAULT 'solicitado',
    importe_propuesto DOUBLE PRECISION,
    importe_aceptado DOUBLE PRECISION,
    email_solicitud_enviado BOOLEAN DEFAULT FALSE,
    fecha_solicitud TIMESTAMP DEFAULT NOW(),
    fecha_envio_presupuesto TIMESTAMP,
    fecha_respuesta TIMESTAMP,
    notas_internas TEXT,
    respuesta_cliente TEXT
);
