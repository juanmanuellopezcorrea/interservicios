-- Migracion inicial: Crear todas las tablas para la app de servicios profesionales
-- Ejecutar en Supabase PostgreSQL

-- Crear tipos ENUM primero
DO $$ BEGIN
    CREATE TYPE modalidad_cuota_enum AS ENUM ('BASICO', 'PLUS', 'PREMIUM', 'SIN_CUOTA');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE tipo_tarea_enum AS ENUM ('CLIENTE', 'INTERNA');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE tipo_limite_enum AS ENUM ('APUNTES', 'HORAS', 'EPIGRAFES', 'NINGUNO');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE clasificacion_facturacion_enum AS ENUM ('INCLUIDA_EN_CUOTA', 'FACTURABLE', 'NO_FACTURABLE', 'LIMITE_SUPERADO', 'TARIFA_MANUAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE periodo_tipo_enum AS ENUM ('MENSUAL', 'ANUAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Tabla trabajadores (debe crearse antes de usuarios por FK)
CREATE TABLE IF NOT EXISTS trabajadores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    coste_hora NUMERIC(10, 2) NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(200) UNIQUE,
    password_hash VARCHAR(255),
    rol VARCHAR(30) NOT NULL DEFAULT 'TRABAJADOR',
    activo BOOLEAN DEFAULT TRUE NOT NULL
);

-- Tabla usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL,
    trabajador_id INTEGER REFERENCES trabajadores(id)
);

-- Tabla clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    cuota_mensual NUMERIC(10, 2) NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modalidad_cuota modalidad_cuota_enum NOT NULL DEFAULT 'SIN_CUOTA',
    precio_cuota_mensual NUMERIC(10, 2),
    epigrafes_iae_contratados INTEGER DEFAULT 0,
    horas_asesoria_fiscal_mes NUMERIC(5, 2) DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    cif VARCHAR(20),
    email VARCHAR(200),
    telefono VARCHAR(20),
    razon_social VARCHAR(300),
    nombre_comercial VARCHAR(200),
    direccion_fiscal VARCHAR(500),
    codigo_postal VARCHAR(10),
    municipio VARCHAR(200),
    provincia VARCHAR(100),
    pais VARCHAR(100) DEFAULT 'España',
    persona_contacto VARCHAR(200),
    cargo_contacto VARCHAR(100),
    telefono_contacto VARCHAR(20),
    email_contacto VARCHAR(200),
    persona_contacto_2 VARCHAR(200),
    telefono_contacto_2 VARCHAR(20),
    email_contacto_2 VARCHAR(200),
    tipo_sociedad VARCHAR(50),
    fecha_constitucion DATE,
    capital_social DOUBLE PRECISION,
    num_socios INTEGER,
    cnae_principal VARCHAR(10),
    cnae_descripcion VARCHAR(500),
    cnae_secundarios TEXT,
    descripcion_actividad TEXT,
    sector VARCHAR(100),
    tiene_empleados BOOLEAN DEFAULT FALSE NOT NULL,
    num_empleados_actual INTEGER DEFAULT 0 NOT NULL,
    prevision_contratacion BOOLEAN DEFAULT FALSE NOT NULL,
    prevision_num_empleados INTEGER DEFAULT 0 NOT NULL,
    prevision_plazo_meses INTEGER,
    empleados_oficina BOOLEAN DEFAULT FALSE NOT NULL,
    empleados_teletrabajo BOOLEAN DEFAULT FALSE NOT NULL,
    empleados_obra BOOLEAN DEFAULT FALSE NOT NULL,
    empleados_vehiculos BOOLEAN DEFAULT FALSE NOT NULL,
    empleados_turnos BOOLEAN DEFAULT FALSE NOT NULL,
    empleados_nocturnos BOOLEAN DEFAULT FALSE NOT NULL,
    convenio_aplicable VARCHAR(300),
    convenio_codigo VARCHAR(50),
    facturacion_anual VARCHAR(50),
    facturacion_estimada DOUBLE PRECISION,
    opera_efectivo VARCHAR(50),
    num_empleados INTEGER DEFAULT 0,
    potencia_climat_kw DOUBLE PRECISION DEFAULT 0,
    trata_datos_especiales BOOLEAN DEFAULT FALSE,
    sector_obligado_blanqueo BOOLEAN DEFAULT FALSE,
    volumen_efectivo_anual DOUBLE PRECISION,
    exporta BOOLEAN DEFAULT FALSE NOT NULL,
    paises_exportacion TEXT,
    tiene_local BOOLEAN DEFAULT FALSE NOT NULL,
    direccion_local VARCHAR(500),
    tipo_local VARCHAR(50),
    superficie_m2 DOUBLE PRECISION,
    num_locales INTEGER DEFAULT 0 NOT NULL,
    tiene_almacen BOOLEAN DEFAULT FALSE NOT NULL,
    almacena_quimicos BOOLEAN DEFAULT FALSE NOT NULL,
    tiene_maquinaria BOOLEAN DEFAULT FALSE NOT NULL,
    manipula_alimentos BOOLEAN DEFAULT FALSE NOT NULL,
    tiene_climatizacion BOOLEAN DEFAULT FALSE NOT NULL,
    potencia_climatizacion_kw DOUBLE PRECISION,
    tiene_ascensor BOOLEAN DEFAULT FALSE NOT NULL,
    tiene_parking BOOLEAN DEFAULT FALSE NOT NULL,
    tiene_web BOOLEAN DEFAULT FALSE NOT NULL,
    url_web VARCHAR(500),
    tiene_rrss BOOLEAN DEFAULT FALSE NOT NULL,
    rrss_activas TEXT,
    tiene_ecommerce BOOLEAN DEFAULT FALSE NOT NULL,
    plataforma_ecommerce VARCHAR(100),
    trata_datos_personales BOOLEAN DEFAULT FALSE NOT NULL,
    volumen_datos VARCHAR(50),
    trata_datos_contacto BOOLEAN DEFAULT FALSE NOT NULL,
    trata_datos_economicos BOOLEAN DEFAULT FALSE NOT NULL,
    trata_datos_salud BOOLEAN DEFAULT FALSE NOT NULL,
    trata_datos_menores BOOLEAN DEFAULT FALSE NOT NULL,
    trata_datos_biometricos BOOLEAN DEFAULT FALSE NOT NULL,
    trata_datos_judicial BOOLEAN DEFAULT FALSE NOT NULL,
    iban VARCHAR(34),
    titular_cuenta VARCHAR(200),
    banco VARCHAR(100),
    forma_pago VARCHAR(50),
    dia_facturacion INTEGER,
    dia_vencimiento INTEGER,
    descuento_aplicable DOUBLE PRECISION DEFAULT 0 NOT NULL,
    observaciones_comerciales TEXT,
    onboarding_completado BOOLEAN DEFAULT FALSE NOT NULL,
    onboarding_fecha_inicio TIMESTAMP,
    onboarding_fecha_fin TIMESTAMP,
    onboarding_paso_actual INTEGER DEFAULT 1 NOT NULL,
    onboarding_porcentaje INTEGER DEFAULT 0 NOT NULL,
    ultimo_analisis_compliance TIMESTAMP,
    proximo_analisis_compliance TIMESTAMP,
    nivel_riesgo_compliance VARCHAR(20),
    compliance_porcentaje INTEGER DEFAULT 0 NOT NULL
);

-- Tabla tareas
CREATE TABLE IF NOT EXISTS tareas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    incluida_contrato BOOLEAN DEFAULT TRUE,
    precio_hora NUMERIC(10, 2),
    tipo_tarea tipo_tarea_enum NOT NULL DEFAULT 'CLIENTE',
    incluida_cuota_basica BOOLEAN DEFAULT FALSE NOT NULL,
    incluida_cuota_estandar BOOLEAN DEFAULT FALSE NOT NULL,
    incluida_cuota_premium BOOLEAN DEFAULT FALSE NOT NULL,
    siempre_facturable BOOLEAN DEFAULT FALSE NOT NULL,
    tipo_limite tipo_limite_enum NOT NULL DEFAULT 'NINGUNO',
    valor_limite INTEGER,
    tarifa_hora_fuera_cuota BOOLEAN DEFAULT FALSE NOT NULL,
    precio_fijo_fuera_cuota NUMERIC(10, 2),
    tarifa_manual BOOLEAN DEFAULT FALSE NOT NULL,
    categoria VARCHAR(100),
    requiere_cliente BOOLEAN DEFAULT TRUE NOT NULL,
    notas TEXT
);

-- Tabla intermedia cliente_tarea
CREATE TABLE IF NOT EXISTS cliente_tarea (
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    tarea_id INTEGER NOT NULL REFERENCES tareas(id) ON DELETE CASCADE,
    PRIMARY KEY (cliente_id, tarea_id)
);

-- Tabla registro_horas
CREATE TABLE IF NOT EXISTS registro_horas (
    id SERIAL PRIMARY KEY,
    trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    tarea_id INTEGER NOT NULL REFERENCES tareas(id),
    fecha DATE NOT NULL,
    horas NUMERIC(5, 2) NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    coste_total NUMERIC(10, 2) NOT NULL,
    importe_facturar NUMERIC(10, 2) NOT NULL DEFAULT 0,
    clasificacion_facturacion clasificacion_facturacion_enum,
    importe_facturable NUMERIC(10, 2),
    importe_manual NUMERIC(10, 2),
    observaciones TEXT
);

-- Tabla plantillas_tarea
CREATE TABLE IF NOT EXISTS plantillas_tarea (
    id SERIAL PRIMARY KEY,
    trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
    nombre VARCHAR(100) NOT NULL,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    tarea_id INTEGER NOT NULL REFERENCES tareas(id),
    horas_default NUMERIC(5, 2) NOT NULL DEFAULT 1,
    descripcion_default TEXT,
    activa BOOLEAN DEFAULT TRUE NOT NULL
);

-- Tabla timer_trabajo
CREATE TABLE IF NOT EXISTS timer_trabajo (
    id SERIAL PRIMARY KEY,
    trabajador_id INTEGER NOT NULL UNIQUE REFERENCES trabajadores(id),
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    tarea_id INTEGER NOT NULL REFERENCES tareas(id),
    nota TEXT,
    started_at TIMESTAMP NOT NULL,
    accumulated_seconds INTEGER NOT NULL DEFAULT 0,
    is_paused BOOLEAN DEFAULT FALSE NOT NULL
);

-- Tabla fichajes_control_horario
CREATE TABLE IF NOT EXISTS fichajes_control_horario (
    id SERIAL PRIMARY KEY,
    trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
    fecha DATE NOT NULL,
    hora_entrada TIME NOT NULL,
    hora_salida TIME,
    horas_trabajadas NUMERIC(6, 2),
    ubicacion VARCHAR(50) NOT NULL DEFAULT 'Oficina',
    estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente'
);

-- Tabla cuestionario_normativo_cliente
CREATE TABLE IF NOT EXISTS cuestionario_normativo_cliente (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL UNIQUE REFERENCES clientes(id),
    respuestas_json TEXT NOT NULL DEFAULT '{}',
    actualizado_en TIMESTAMP
);

-- Tabla control_limites
CREATE TABLE IF NOT EXISTS control_limites (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    tarea_id INTEGER NOT NULL REFERENCES tareas(id),
    periodo_tipo periodo_tipo_enum NOT NULL,
    mes INTEGER,
    anio INTEGER NOT NULL,
    consumo_acumulado NUMERIC(10, 2) NOT NULL DEFAULT 0,
    limite_excedido BOOLEAN DEFAULT FALSE NOT NULL,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (cliente_id, tarea_id, periodo_tipo, mes, anio)
);

-- Tabla catalogo_obligaciones_legacy
CREATE TABLE IF NOT EXISTS catalogo_obligaciones_legacy (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    categoria VARCHAR(100),
    descripcion TEXT,
    normativa VARCHAR(500),
    condiciones_json TEXT,
    items_json TEXT,
    obligatoria BOOLEAN DEFAULT TRUE NOT NULL,
    recomendada BOOLEAN DEFAULT FALSE NOT NULL,
    plazo VARCHAR(100),
    sancion_min DOUBLE PRECISION,
    sancion_max DOUBLE PRECISION,
    sancion_descripcion TEXT,
    orden_prioridad INTEGER DEFAULT 999 NOT NULL,
    activa BOOLEAN DEFAULT TRUE NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP
);

-- Tabla obligacion_cliente_legacy
CREATE TABLE IF NOT EXISTS obligacion_cliente_legacy (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    catalogo_id INTEGER NOT NULL REFERENCES catalogo_obligaciones_legacy(id),
    estado VARCHAR(50) DEFAULT 'pendiente' NOT NULL,
    porcentaje_cumplimiento INTEGER DEFAULT 0 NOT NULL,
    items_estado_json TEXT,
    fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_cumplimiento TIMESTAMP,
    fecha_vencimiento TIMESTAMP,
    incluir_en_email BOOLEAN DEFAULT TRUE NOT NULL,
    presupuesto_solicitado BOOLEAN DEFAULT FALSE NOT NULL,
    fecha_solicitud_presupuesto TIMESTAMP,
    presupuesto_enviado BOOLEAN DEFAULT FALSE NOT NULL,
    fecha_envio_presupuesto TIMESTAMP,
    importe_presupuesto DOUBLE PRECISION,
    observaciones TEXT
);

-- Tabla documento_onboarding
CREATE TABLE IF NOT EXISTS documento_onboarding (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    tipo VARCHAR(100),
    nombre VARCHAR(200) NOT NULL,
    categoria VARCHAR(50),
    obligatorio BOOLEAN DEFAULT TRUE NOT NULL,
    orden INTEGER,
    estado VARCHAR(50) DEFAULT 'pendiente' NOT NULL,
    archivo_nombre VARCHAR(500),
    archivo_path VARCHAR(1000),
    archivo_size INTEGER,
    archivo_tipo VARCHAR(50),
    fecha_subida TIMESTAMP,
    fecha_validacion TIMESTAMP,
    fecha_vencimiento TIMESTAMP,
    subido_por_id INTEGER REFERENCES usuarios(id),
    validado_por_id INTEGER REFERENCES usuarios(id),
    observaciones TEXT,
    motivo_rechazo TEXT
);

-- Tabla informe_compliance
CREATE TABLE IF NOT EXISTS informe_compliance (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    tipo VARCHAR(50),
    total_obligaciones INTEGER,
    obligaciones_cumplidas INTEGER,
    obligaciones_pendientes INTEGER,
    obligaciones_en_proceso INTEGER,
    obligaciones_no_aplican INTEGER,
    porcentaje_cumplimiento INTEGER,
    nivel_riesgo VARCHAR(20),
    email_generado BOOLEAN DEFAULT FALSE NOT NULL,
    email_contenido TEXT,
    email_enviado BOOLEAN DEFAULT FALSE NOT NULL,
    fecha_envio_email TIMESTAMP,
    email_abierto BOOLEAN DEFAULT FALSE NOT NULL,
    fecha_apertura_email TIMESTAMP,
    num_presupuestos_solicitados INTEGER DEFAULT 0 NOT NULL,
    servicios_solicitados TEXT,
    generado_por_id INTEGER REFERENCES usuarios(id),
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT
);

-- Tabla alerta_compliance
CREATE TABLE IF NOT EXISTS alerta_compliance (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    tipo VARCHAR(50),
    prioridad VARCHAR(20),
    titulo VARCHAR(300) NOT NULL,
    descripcion TEXT,
    estado VARCHAR(50) DEFAULT 'pendiente' NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento TIMESTAMP,
    fecha_resolucion TIMESTAMP,
    asignado_a_id INTEGER REFERENCES usuarios(id),
    resuelto_por_id INTEGER REFERENCES usuarios(id),
    observaciones_resolucion TEXT
);

-- Crear indices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_registro_horas_trabajador ON registro_horas(trabajador_id);
CREATE INDEX IF NOT EXISTS idx_registro_horas_cliente ON registro_horas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_registro_horas_fecha ON registro_horas(fecha);
CREATE INDEX IF NOT EXISTS idx_clientes_activo ON clientes(activo);
CREATE INDEX IF NOT EXISTS idx_trabajadores_activo ON trabajadores(activo);
CREATE INDEX IF NOT EXISTS idx_fichajes_trabajador_fecha ON fichajes_control_horario(trabajador_id, fecha);
