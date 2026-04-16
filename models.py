from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Enum as SQLEnum
from decimal import Decimal
import json
db = SQLAlchemy()

cliente_tarea = db.Table(
    "cliente_tarea",
    db.Column("cliente_id", db.Integer, db.ForeignKey("clientes.id"), primary_key=True),
    db.Column("tarea_id", db.Integer, db.ForeignKey("tareas.id"), primary_key=True),
)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # 'ADMIN' o 'TRABAJADOR'
    trabajador_id = db.Column(db.Integer, db.ForeignKey('trabajadores.id'), nullable=True)
    
    trabajador = db.relationship('Trabajador', backref='usuario', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    cuota_mensual = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Nuevos campos para modalidades de cuota
    modalidad_cuota = db.Column(
        SQLEnum('BASICO', 'PLUS', 'PREMIUM', 'SIN_CUOTA', name='modalidad_cuota_enum'),
        nullable=False,
        default='SIN_CUOTA'
    )
    precio_cuota_mensual = db.Column(db.Numeric(10, 2), nullable=True)
    epigrafes_iae_contratados = db.Column(db.Integer, nullable=True, default=0)
    horas_asesoria_fiscal_mes = db.Column(db.Numeric(5, 2), nullable=True, default=0)

    # --- Compliance / onboarding (España); columnas nullable para BD existentes ---
    activo = db.Column(db.Boolean, default=True, nullable=False)
    cif = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    razon_social = db.Column(db.String(300), nullable=True)
    nombre_comercial = db.Column(db.String(200), nullable=True)
    direccion_fiscal = db.Column(db.String(500), nullable=True)
    codigo_postal = db.Column(db.String(10), nullable=True)
    municipio = db.Column(db.String(200), nullable=True)
    provincia = db.Column(db.String(100), nullable=True)
    pais = db.Column(db.String(100), nullable=True, default='España')
    persona_contacto = db.Column(db.String(200), nullable=True)
    cargo_contacto = db.Column(db.String(100), nullable=True)
    telefono_contacto = db.Column(db.String(20), nullable=True)
    email_contacto = db.Column(db.String(200), nullable=True)
    persona_contacto_2 = db.Column(db.String(200), nullable=True)
    telefono_contacto_2 = db.Column(db.String(20), nullable=True)
    email_contacto_2 = db.Column(db.String(200), nullable=True)
    tipo_sociedad = db.Column(db.String(50), nullable=True)
    fecha_constitucion = db.Column(db.Date, nullable=True)
    capital_social = db.Column(db.Float, nullable=True)
    num_socios = db.Column(db.Integer, nullable=True)
    cnae_principal = db.Column(db.String(10), nullable=True)
    cnae_descripcion = db.Column(db.String(500), nullable=True)
    cnae_secundarios = db.Column(db.Text, nullable=True)
    descripcion_actividad = db.Column(db.Text, nullable=True)
    sector = db.Column(db.String(100), nullable=True)
    tiene_empleados = db.Column(db.Boolean, default=False, nullable=False)
    num_empleados_actual = db.Column(db.Integer, default=0, nullable=False)
    prevision_contratacion = db.Column(db.Boolean, default=False, nullable=False)
    prevision_num_empleados = db.Column(db.Integer, default=0, nullable=False)
    prevision_plazo_meses = db.Column(db.Integer, nullable=True)
    empleados_oficina = db.Column(db.Boolean, default=False, nullable=False)
    empleados_teletrabajo = db.Column(db.Boolean, default=False, nullable=False)
    empleados_obra = db.Column(db.Boolean, default=False, nullable=False)
    empleados_vehiculos = db.Column(db.Boolean, default=False, nullable=False)
    empleados_turnos = db.Column(db.Boolean, default=False, nullable=False)
    empleados_nocturnos = db.Column(db.Boolean, default=False, nullable=False)
    convenio_aplicable = db.Column(db.String(300), nullable=True)
    convenio_codigo = db.Column(db.String(50), nullable=True)
    facturacion_anual = db.Column(db.String(50), nullable=True)
    facturacion_estimada = db.Column(db.Float, nullable=True)
    opera_efectivo = db.Column(db.String(50), nullable=True)
    # Campos nuevos (solo si no existían ya en el modelo): motor compliance_engine.py
    num_empleados = db.Column(db.Integer, default=0)
    potencia_climat_kw = db.Column(db.Float, default=0)
    trata_datos_especiales = db.Column(db.Boolean, default=False)
    sector_obligado_blanqueo = db.Column(db.Boolean, default=False)
    volumen_efectivo_anual = db.Column(db.Float, nullable=True)
    exporta = db.Column(db.Boolean, default=False, nullable=False)
    paises_exportacion = db.Column(db.Text, nullable=True)
    tiene_local = db.Column(db.Boolean, default=False, nullable=False)
    direccion_local = db.Column(db.String(500), nullable=True)
    tipo_local = db.Column(db.String(50), nullable=True)
    superficie_m2 = db.Column(db.Float, nullable=True)
    num_locales = db.Column(db.Integer, default=0, nullable=False)
    tiene_almacen = db.Column(db.Boolean, default=False, nullable=False)
    almacena_quimicos = db.Column(db.Boolean, default=False, nullable=False)
    tiene_maquinaria = db.Column(db.Boolean, default=False, nullable=False)
    manipula_alimentos = db.Column(db.Boolean, default=False, nullable=False)
    tiene_climatizacion = db.Column(db.Boolean, default=False, nullable=False)
    potencia_climatizacion_kw = db.Column(db.Float, nullable=True)
    tiene_ascensor = db.Column(db.Boolean, default=False, nullable=False)
    tiene_parking = db.Column(db.Boolean, default=False, nullable=False)
    tiene_web = db.Column(db.Boolean, default=False, nullable=False)
    url_web = db.Column(db.String(500), nullable=True)
    tiene_rrss = db.Column(db.Boolean, default=False, nullable=False)
    rrss_activas = db.Column(db.Text, nullable=True)
    tiene_ecommerce = db.Column(db.Boolean, default=False, nullable=False)
    plataforma_ecommerce = db.Column(db.String(100), nullable=True)
    trata_datos_personales = db.Column(db.Boolean, default=False, nullable=False)
    volumen_datos = db.Column(db.String(50), nullable=True)
    trata_datos_contacto = db.Column(db.Boolean, default=False, nullable=False)
    trata_datos_economicos = db.Column(db.Boolean, default=False, nullable=False)
    trata_datos_salud = db.Column(db.Boolean, default=False, nullable=False)
    trata_datos_menores = db.Column(db.Boolean, default=False, nullable=False)
    trata_datos_biometricos = db.Column(db.Boolean, default=False, nullable=False)
    trata_datos_judicial = db.Column(db.Boolean, default=False, nullable=False)
    iban = db.Column(db.String(34), nullable=True)
    titular_cuenta = db.Column(db.String(200), nullable=True)
    banco = db.Column(db.String(100), nullable=True)
    forma_pago = db.Column(db.String(50), nullable=True)
    dia_facturacion = db.Column(db.Integer, nullable=True)
    dia_vencimiento = db.Column(db.Integer, nullable=True)
    descuento_aplicable = db.Column(db.Float, default=0, nullable=False)
    observaciones_comerciales = db.Column(db.Text, nullable=True)
    onboarding_completado = db.Column(db.Boolean, default=False, nullable=False)
    onboarding_fecha_inicio = db.Column(db.DateTime, nullable=True)
    onboarding_fecha_fin = db.Column(db.DateTime, nullable=True)
    onboarding_paso_actual = db.Column(db.Integer, default=1, nullable=False)
    onboarding_porcentaje = db.Column(db.Integer, default=0, nullable=False)
    ultimo_analisis_compliance = db.Column(db.DateTime, nullable=True)
    proximo_analisis_compliance = db.Column(db.DateTime, nullable=True)
    nivel_riesgo_compliance = db.Column(db.String(20), nullable=True)
    compliance_porcentaje = db.Column(db.Integer, default=0, nullable=False)

    horas = db.relationship('RegistroHora', backref='cliente', lazy=True)
    controles_limites = db.relationship('ControlLimites', backref='cliente', lazy=True, cascade='all, delete-orphan')

    tareas_incluidas = db.relationship(
        "Tarea",
        secondary=cliente_tarea,
        lazy="subquery",
        backref=db.backref("clientes", lazy=True)
    )

    cuestionario_normativo = db.relationship(
        'CuestionarioNormativoCliente',
        back_populates='cliente',
        cascade='all, delete-orphan',
        uselist=False,
    )

    # Onboarding eliminado por requerimiento

    # Relaciones del módulo compliance anterior (legacy). No afectan al sistema de horas.
    obligaciones_compliance = db.relationship(
        'ObligacionClienteLegacy',
        back_populates='cliente',
        cascade='all, delete-orphan',
        lazy='dynamic',
    )
    documentos_onboarding = db.relationship(
        'DocumentoOnboarding',
        back_populates='cliente',
        cascade='all, delete-orphan',
        lazy='dynamic',
    )
    informes_compliance = db.relationship(
        'InformeCompliance',
        back_populates='cliente',
        cascade='all, delete-orphan',
        lazy='dynamic',
    )
    alertas_compliance = db.relationship(
        'AlertaCompliance',
        back_populates='cliente',
        cascade='all, delete-orphan',
        lazy='dynamic',
    )

    def get_tipo_sociedad_display(self):
        labels = {
            'autonomo': 'Autónomo',
            'sl': 'S.L.',
            'sa': 'S.A.',
            'cooperativa': 'Cooperativa',
            'comunidad_bienes': 'Comunidad de bienes',
            'asociacion': 'Asociación',
            'fundacion': 'Fundación',
        }
        if not self.tipo_sociedad:
            return '—'
        return labels.get(self.tipo_sociedad, self.tipo_sociedad)


class Trabajador(db.Model):
    __tablename__ = 'trabajadores'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    coste_hora = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Login y rol (sistema de permisos)
    email = db.Column(db.String(200), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    rol = db.Column(db.String(30), nullable=False, default='TRABAJADOR')  # ADMIN, TRABAJADOR, TRABAJADOR_FACTURACION
    activo = db.Column(db.Boolean, default=True, nullable=False)
    
    horas = db.relationship('RegistroHora', backref='trabajador', lazy=True)
    
    def set_password(self, password):
        if password:
            self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def es_admin(self):
        return self.rol == 'ADMIN'
    
    def es_trabajador(self):
        return self.rol == 'TRABAJADOR'

    def es_trabajador_facturacion(self):
        return self.rol == 'TRABAJADOR_FACTURACION'

class Tarea(db.Model):
    __tablename__ = 'tareas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campos antiguos (mantenidos para compatibilidad durante migración)
    incluida_contrato = db.Column(db.Boolean, nullable=True, default=True)
    precio_hora = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Nuevos campos del sistema de facturación complejo
    tipo_tarea = db.Column(
        SQLEnum('CLIENTE', 'INTERNA', name='tipo_tarea_enum'),
        nullable=False,
        default='CLIENTE'
    )
    incluida_cuota_basica = db.Column(db.Boolean, nullable=False, default=False)
    incluida_cuota_estandar = db.Column(db.Boolean, nullable=False, default=False)
    incluida_cuota_premium = db.Column(db.Boolean, nullable=False, default=False)
    siempre_facturable = db.Column(db.Boolean, nullable=False, default=False)
    tipo_limite = db.Column(
        SQLEnum('APUNTES', 'HORAS', 'EPIGRAFES', 'NINGUNO', name='tipo_limite_enum'),
        nullable=False,
        default='NINGUNO'
    )
    valor_limite = db.Column(db.Integer, nullable=True)
    tarifa_hora_fuera_cuota = db.Column(db.Boolean, nullable=False, default=False)
    precio_fijo_fuera_cuota = db.Column(db.Numeric(10, 2), nullable=True)
    tarifa_manual = db.Column(db.Boolean, nullable=False, default=False)
    categoria = db.Column(db.String(100), nullable=True)
    requiere_cliente = db.Column(db.Boolean, nullable=False, default=True)
    notas = db.Column(db.Text, nullable=True)
    
    horas = db.relationship('RegistroHora', backref='tarea', lazy=True)
    controles_limites = db.relationship('ControlLimites', backref='tarea', lazy=True, cascade='all, delete-orphan')

class RegistroHora(db.Model):
    __tablename__ = 'registro_horas'
    
    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey('trabajadores.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tarea_id = db.Column(db.Integer, db.ForeignKey('tareas.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    horas = db.Column(db.Numeric(5, 2), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campos calculados almacenados para auditoría
    coste_total = db.Column(db.Numeric(10, 2), nullable=False)
    importe_facturar = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Nuevos campos de clasificación de facturación
    clasificacion_facturacion = db.Column(
        SQLEnum(
            'INCLUIDA_EN_CUOTA',
            'FACTURABLE',
            'NO_FACTURABLE',
            'LIMITE_SUPERADO',
            'TARIFA_MANUAL',
            name='clasificacion_facturacion_enum'
        ),
        nullable=True
    )
    importe_facturable = db.Column(db.Numeric(10, 2), nullable=True)
    importe_manual = db.Column(db.Numeric(10, 2), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)


class PlantillaTarea(db.Model):
    """Plantilla personal de registro rápido (por trabajador)."""
    __tablename__ = 'plantillas_tarea'

    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey('trabajadores.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tarea_id = db.Column(db.Integer, db.ForeignKey('tareas.id'), nullable=False)
    horas_default = db.Column(db.Numeric(5, 2), nullable=False, default=1)
    descripcion_default = db.Column(db.Text, nullable=True)
    activa = db.Column(db.Boolean, nullable=False, default=True)

    trabajador = db.relationship('Trabajador', backref=db.backref('plantillas_tarea', lazy='dynamic'))
    cliente = db.relationship('Cliente')
    tarea = db.relationship('Tarea')


class TimerTrabajo(db.Model):
    """Un temporizador activo por trabajador (registro de horas por cliente/tarea)."""
    __tablename__ = 'timer_trabajo'

    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey('trabajadores.id'), nullable=False, unique=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tarea_id = db.Column(db.Integer, db.ForeignKey('tareas.id'), nullable=False)
    nota = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=False)
    accumulated_seconds = db.Column(db.Integer, nullable=False, default=0)
    is_paused = db.Column(db.Boolean, nullable=False, default=False)

    trabajador = db.relationship('Trabajador', backref=db.backref('timer_trabajo', uselist=False))
    cliente = db.relationship('Cliente')
    tarea = db.relationship('Tarea')


class FichajeControlHorario(db.Model):
    """Fichajes de entrada/salida para control horario (formato Holded)."""
    __tablename__ = 'fichajes_control_horario'

    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey('trabajadores.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_entrada = db.Column(db.Time, nullable=False)
    hora_salida = db.Column(db.Time, nullable=True)  # None si está fichado (en curso)
    horas_trabajadas = db.Column(db.Numeric(6, 2), nullable=True)  # Decimal, calculado al cerrar
    ubicacion = db.Column(db.String(50), nullable=False, default='Oficina')
    estado = db.Column(db.String(20), nullable=False, default='Pendiente')  # Pendiente | Aprobado

    trabajador = db.relationship('Trabajador', backref=db.backref('fichajes_control_horario', lazy='dynamic'))


class CuestionarioNormativoCliente(db.Model):
    """Cuestionario normativo SI/NO/PTE por cliente."""
    __tablename__ = 'cuestionario_normativo_cliente'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False, unique=True)
    respuestas_json = db.Column(db.Text, nullable=False, default='{}')  # {item_id: 'SI'|'NO'|'PTE'|''}
    actualizado_en = db.Column(db.DateTime, nullable=True)

    cliente = db.relationship('Cliente', back_populates='cuestionario_normativo')

    def get_respuestas(self):
        try:
            return json.loads(self.respuestas_json or '{}')
        except Exception:
            return {}

    def set_respuestas(self, data: dict):
        self.respuestas_json = json.dumps(data or {}, ensure_ascii=False)
        self.actualizado_en = datetime.utcnow()




class ControlLimites(db.Model):
    __tablename__ = 'control_limites'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tarea_id = db.Column(db.Integer, db.ForeignKey('tareas.id'), nullable=False)
    periodo_tipo = db.Column(
        SQLEnum('MENSUAL', 'ANUAL', name='periodo_tipo_enum'),
        nullable=False
    )
    mes = db.Column(db.Integer, nullable=True)  # 1-12 para mensual, NULL para anual
    anio = db.Column(db.Integer, nullable=False)
    consumo_acumulado = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    limite_excedido = db.Column(db.Boolean, nullable=False, default=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('cliente_id', 'tarea_id', 'periodo_tipo', 'mes', 'anio', name='uq_control_limites'),
    )


class CatalogoObligaciones(db.Model):
    """Catálogo maestro de obligaciones legales (referencia España)."""
    __tablename__ = 'catalogo_obligaciones_legacy'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(100), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    normativa = db.Column(db.String(500), nullable=True)
    condiciones_json = db.Column(db.Text, nullable=True)
    items_json = db.Column(db.Text, nullable=True)
    obligatoria = db.Column(db.Boolean, default=True, nullable=False)
    recomendada = db.Column(db.Boolean, default=False, nullable=False)
    plazo = db.Column(db.String(100), nullable=True)
    sancion_min = db.Column(db.Float, nullable=True)
    sancion_max = db.Column(db.Float, nullable=True)
    sancion_descripcion = db.Column(db.Text, nullable=True)
    orden_prioridad = db.Column(db.Integer, default=999, nullable=False)
    activa = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, onupdate=datetime.utcnow)

    obligaciones_cliente = db.relationship(
        'ObligacionClienteLegacy', back_populates='catalogo', lazy='dynamic'
    )

    def get_items(self):
        try:
            return json.loads(self.items_json or '[]')
        except (json.JSONDecodeError, TypeError):
            return []


class ObligacionClienteLegacy(db.Model):
    __tablename__ = 'obligacion_cliente_legacy'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    catalogo_id = db.Column(db.Integer, db.ForeignKey('catalogo_obligaciones_legacy.id'), nullable=False)
    estado = db.Column(db.String(50), default='pendiente', nullable=False)
    porcentaje_cumplimiento = db.Column(db.Integer, default=0, nullable=False)
    items_estado_json = db.Column(db.Text, nullable=True)
    fecha_aplicacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_cumplimiento = db.Column(db.DateTime, nullable=True)
    fecha_vencimiento = db.Column(db.DateTime, nullable=True)
    incluir_en_email = db.Column(db.Boolean, default=True, nullable=False)
    presupuesto_solicitado = db.Column(db.Boolean, default=False, nullable=False)
    fecha_solicitud_presupuesto = db.Column(db.DateTime, nullable=True)
    presupuesto_enviado = db.Column(db.Boolean, default=False, nullable=False)
    fecha_envio_presupuesto = db.Column(db.DateTime, nullable=True)
    importe_presupuesto = db.Column(db.Float, nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    cliente = db.relationship('Cliente', back_populates='obligaciones_compliance')
    catalogo = db.relationship('CatalogoObligaciones', back_populates='obligaciones_cliente')

    def get_items_estado(self):
        try:
            return json.loads(self.items_estado_json or '{}')
        except (json.JSONDecodeError, TypeError):
            return {}


# Alias de compatibilidad para imports legacy (evita romper compliance_service.py).
ObligacionCliente = ObligacionClienteLegacy


class DocumentoOnboarding(db.Model):
    __tablename__ = 'documento_onboarding'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo = db.Column(db.String(100), nullable=True)
    nombre = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50), nullable=True)
    obligatorio = db.Column(db.Boolean, default=True, nullable=False)
    orden = db.Column(db.Integer, nullable=True)
    estado = db.Column(db.String(50), default='pendiente', nullable=False)
    archivo_nombre = db.Column(db.String(500), nullable=True)
    archivo_path = db.Column(db.String(1000), nullable=True)
    archivo_size = db.Column(db.Integer, nullable=True)
    archivo_tipo = db.Column(db.String(50), nullable=True)
    fecha_subida = db.Column(db.DateTime, nullable=True)
    fecha_validacion = db.Column(db.DateTime, nullable=True)
    fecha_vencimiento = db.Column(db.DateTime, nullable=True)
    subido_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    validado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    motivo_rechazo = db.Column(db.Text, nullable=True)

    cliente = db.relationship('Cliente', back_populates='documentos_onboarding')
    subido_por = db.relationship('Usuario', foreign_keys=[subido_por_id])
    validado_por = db.relationship('Usuario', foreign_keys=[validado_por_id])


class InformeCompliance(db.Model):
    __tablename__ = 'informe_compliance'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=True)
    total_obligaciones = db.Column(db.Integer, nullable=True)
    obligaciones_cumplidas = db.Column(db.Integer, nullable=True)
    obligaciones_pendientes = db.Column(db.Integer, nullable=True)
    obligaciones_en_proceso = db.Column(db.Integer, nullable=True)
    obligaciones_no_aplican = db.Column(db.Integer, nullable=True)
    porcentaje_cumplimiento = db.Column(db.Integer, nullable=True)
    nivel_riesgo = db.Column(db.String(20), nullable=True)
    email_generado = db.Column(db.Boolean, default=False, nullable=False)
    email_contenido = db.Column(db.Text, nullable=True)
    email_enviado = db.Column(db.Boolean, default=False, nullable=False)
    fecha_envio_email = db.Column(db.DateTime, nullable=True)
    email_abierto = db.Column(db.Boolean, default=False, nullable=False)
    fecha_apertura_email = db.Column(db.DateTime, nullable=True)
    num_presupuestos_solicitados = db.Column(db.Integer, default=0, nullable=False)
    servicios_solicitados = db.Column(db.Text, nullable=True)
    generado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones = db.Column(db.Text, nullable=True)

    cliente = db.relationship('Cliente', back_populates='informes_compliance')
    generado_por = db.relationship('Usuario', foreign_keys=[generado_por_id])


class AlertaCompliance(db.Model):
    __tablename__ = 'alerta_compliance'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=True)
    prioridad = db.Column(db.String(20), nullable=True)
    titulo = db.Column(db.String(300), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(50), default='pendiente', nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_vencimiento = db.Column(db.DateTime, nullable=True)
    fecha_resolucion = db.Column(db.DateTime, nullable=True)
    asignado_a_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    resuelto_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    observaciones_resolucion = db.Column(db.Text, nullable=True)

    cliente = db.relationship('Cliente', back_populates='alertas_compliance')
    asignado_a = db.relationship('Usuario', foreign_keys=[asignado_a_id])
    resuelto_por = db.relationship('Usuario', foreign_keys=[resuelto_por_id])