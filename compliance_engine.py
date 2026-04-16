import json
from datetime import datetime
from models import db

class CatalogoObligacion(db.Model):
    __tablename__ = 'catalogo_obligacion'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    normativa = db.Column(db.String(500))
    items_json = db.Column(db.Text)
    obligatoria = db.Column(db.Boolean, default=True)
    plazo = db.Column(db.String(200))
    sancion_min = db.Column(db.Float, default=0)
    sancion_max = db.Column(db.Float, default=0)
    sancion_desc = db.Column(db.Text)
    orden_prioridad = db.Column(db.Integer, default=999)
    activa = db.Column(db.Boolean, default=True)

    def get_items(self):
        try:
            return json.loads(self.items_json)
        except:
            return []

class ObligacionCliente(db.Model):
    __tablename__ = 'obligacion_cliente'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    catalogo_id = db.Column(db.Integer, db.ForeignKey('catalogo_obligacion.id'), nullable=False)
    estado = db.Column(db.String(50), default='pendiente')
    porcentaje_cumplimiento = db.Column(db.Integer, default=0)
    items_estado_json = db.Column(db.Text)
    incluir_en_email = db.Column(db.Boolean, default=True)
    fecha_aplicacion = db.Column(db.DateTime, default=datetime.now)
    fecha_cumplimiento = db.Column(db.DateTime)
    observaciones = db.Column(db.Text)
    catalogo = db.relationship('CatalogoObligacion')

    def get_items_estado(self):
        try:
            return json.loads(self.items_estado_json)
        except:
            return {}

    def calcular_porcentaje(self):
        estados = self.get_items_estado()
        if not estados:
            return 0
        cumplidos = sum(1 for v in estados.values() if v == 'cumplido')
        return int(cumplidos / len(estados) * 100)

class SolicitudPresupuesto(db.Model):
    __tablename__ = 'solicitud_presupuesto'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    obligacion_id = db.Column(db.Integer, db.ForeignKey('obligacion_cliente.id'))
    catalogo_id = db.Column(db.Integer, db.ForeignKey('catalogo_obligacion.id'))
    estado = db.Column(db.String(50), default='solicitado')
    importe_propuesto = db.Column(db.Float)
    importe_aceptado = db.Column(db.Float)
    email_solicitud_enviado = db.Column(db.Boolean, default=False)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.now)
    fecha_envio_presupuesto = db.Column(db.DateTime)
    fecha_respuesta = db.Column(db.DateTime)
    notas_internas = db.Column(db.Text)
    respuesta_cliente = db.Column(db.Text)
    catalogo = db.relationship('CatalogoObligacion')

    def get_estado_badge(self):
        return {'solicitado':'warning','en_preparacion':'info','enviado':'primary','aceptado':'success','rechazado':'danger','cerrado':'secondary'}.get(self.estado,'secondary')

    def get_estado_display(self):
        return {'solicitado':'Solicitado','en_preparacion':'En preparación','enviado':'Presupuesto enviado','aceptado':'Aceptado','rechazado':'Rechazado','cerrado':'Cerrado'}.get(self.estado, self.estado)

CATALOGO = [
    {'codigo':'RGPD','nombre':'Protección de Datos (RGPD / LOPDGDD)','categoria':'proteccion_datos','normativa':'Reglamento UE 2016/679 · LO 3/2018','items_json':json.dumps(['Registro de Actividades de Tratamiento (art. 30 RGPD)','Política de Privacidad publicada','Cláusulas informativas a interesados (art. 13-14 RGPD)','Contratos con Encargados de Tratamiento (art. 28 RGPD)','Análisis de Riesgos','Procedimiento de Brechas de Seguridad (art. 33-34 RGPD)']),'obligatoria':True,'plazo':'INMEDIATO','sancion_min':0,'sancion_max':20000000,'sancion_desc':'Hasta 20.000.000€ o el 4% de la facturación anual global. Competencia de la AEPD.','orden_prioridad':1},
    {'codigo':'PRL','nombre':'Prevención de Riesgos Laborales','categoria':'laboral','normativa':'Ley 31/1995 · RD 39/1997 Reglamento de los Servicios de Prevención','items_json':json.dumps(['Modalidad preventiva elegida y documentada (art. 10 RD 39/1997)','Evaluación de Riesgos de cada puesto (art. 16 LPRL)','Planificación de la Actividad Preventiva','Vigilancia de la Salud — reconocimientos médicos (art. 22 LPRL)','Formación e información a trabajadores (arts. 18-19 LPRL)','Equipos de Protección Individual si procede']),'obligatoria':True,'plazo':'Antes del primer empleado','sancion_min':8195,'sancion_max':983736,'sancion_desc':'Graves: 2.046€–40.985€. Muy graves: 40.986€–819.780€. Recargo prestaciones 30-50% (art. 164 TRLGSS).','orden_prioridad':2},
    {'codigo':'REG_HORARIO','nombre':'Registro Horario Obligatorio','categoria':'laboral','normativa':'Art. 34.9 ET · RDL 8/2019 · Criterio técnico ITSS 101/2019','items_json':json.dumps(['Sistema de fichaje diario (hora entrada y salida)','Conservación de registros durante 4 años (art. 34.9 ET)','Disponible para la Inspección de Trabajo','Accesible para representantes de los trabajadores']),'obligatoria':True,'plazo':'INMEDIATO — vigente desde 12/05/2019','sancion_min':751,'sancion_max':7500,'sancion_desc':'Infracción grave art. 7.5 TRLISOS: 751€–7.500€.','orden_prioridad':3},
    {'codigo':'REG_SALARIAL','nombre':'Registro Salarial — Igualdad Retributiva','categoria':'laboral','normativa':'RD 902/2020 · Art. 28.2 ET · LO 3/2007','items_json':json.dumps(['Registro retributivo desagregado por sexo, grupo, categoría y puesto','Valores medios de salarios y complementos','Justificación documentada si la brecha supera el 25%','Actualización anual y acceso a representantes']),'obligatoria':True,'plazo':'Vigente desde 14/04/2021','sancion_min':751,'sancion_max':7500,'sancion_desc':'Infracción grave art. 7.13 TRLISOS: 751€–7.500€. Puede conllevar exclusión de ayudas públicas.','orden_prioridad':4},
    {'codigo':'PLAN_IGUALDAD','nombre':'Plan de Igualdad','categoria':'laboral','normativa':'Art. 45-49 LO 3/2007 · RD 901/2020 · Registro REGCON','items_json':json.dumps(['Diagnóstico de situación de la empresa','Negociación con representación legal de trabajadores','Redacción e implantación del Plan','Inscripción en el Registro REGCON','Seguimiento, evaluación y revisión periódica']),'obligatoria':True,'plazo':'Obligatorio desde 07/03/2022 para empresas ≥50 trabajadores','sancion_min':6251,'sancion_max':187515,'sancion_desc':'Infracción muy grave art. 8.17 TRLISOS: 6.251€–187.515€. Pérdida de bonificaciones.','orden_prioridad':5},
    {'codigo':'CANAL_DENUNCIAS','nombre':'Canal de Denuncias — Whistleblowing','categoria':'compliance','normativa':'Ley 2/2023, de 20 de febrero','items_json':json.dumps(['Canal interno seguro y confidencial (art. 5 Ley 2/2023)','Garantía de confidencialidad del informante','Procedimiento: acuse en 7 días, resolución en 3 meses','Prohibición expresa de represalias (art. 36)','Información y formación a trabajadores']),'obligatoria':True,'plazo':'Vigente desde 01/12/2023 para empresas ≥50 trabajadores','sancion_min':1001,'sancion_max':1000000,'sancion_desc':'Muy graves hasta 1.000.000€ · Graves: 100.001€–300.000€ · Leves: 1.001€–100.000€.','orden_prioridad':6},
    {'codigo':'LIC_APERTURA','nombre':'Licencia de Apertura / Comunicación de Actividad','categoria':'local','normativa':'Ley 7/1985 LRBRL · Ley 17/2009 · Ordenanzas municipales','items_json':json.dumps(['Licencia de Apertura o Declaración Responsable vigente','Certificado de Instalación Eléctrica (BT) en vigor','Certificado de Instalación de Gas si procede','Inspección de Climatización si >70 kW (RD 931/2021)','Señalización de emergencias y extintor (CTE-DB-SI)']),'obligatoria':True,'plazo':'Antes de iniciar la actividad','sancion_min':300,'sancion_max':3000,'sancion_desc':'Ordenanza Municipal: 300€–3.000€. Puede conllevar precinto cautelar del local.','orden_prioridad':7},
    {'codigo':'SEG_RC','nombre':'Seguro de Responsabilidad Civil','categoria':'seguros','normativa':'Ley 20/2015 de Ordenación del Seguro Privado','items_json':json.dumps(['Póliza RC General vigente con capital suficiente','RC Patronal si hay trabajadores','RC Productos/Trabajos terminados si procede','Renovación anual y actualización de capitales']),'obligatoria':False,'plazo':'MUY RECOMENDADO — obligatorio en numerosos sectores','sancion_min':0,'sancion_max':0,'sancion_desc':'Sin sanción directa, pero riesgo patrimonial total. Obligatorio en: construcción, sanidad, transporte, hostelería, profesiones reguladas.','orden_prioridad':8},
    {'codigo':'SEG_CONVENIO','nombre':'Seguro Colectivo de Convenio','categoria':'seguros','normativa':'Art. 82-92 ET — Convenio Colectivo aplicable','items_json':json.dumps(['Identificación de cobertura mínima exigida por el Convenio','Póliza colectiva contratada (vida, invalidez, accidentes)','Comunicación a trabajadores y actualización de beneficiarios','Renovación según periodicidad del Convenio']),'obligatoria':True,'plazo':'Según el Convenio Colectivo aplicable','sancion_min':751,'sancion_max':7500,'sancion_desc':'Infracción grave art. 7.1 TRLISOS: 751€–7.500€. Más reclamación individual de cada trabajador.','orden_prioridad':9},
    {'codigo':'COMPLIANCE_PENAL','nombre':'Programa de Compliance Penal','categoria':'compliance','normativa':'Arts. 31 bis a 31 quinquies CP · LO 1/2015 · Circular FGE 1/2016','items_json':json.dumps(['Mapa de riesgos penales de la empresa','Código Ético / Código de Conducta','Protocolos de prevención por cada riesgo','Canal de Denuncias interno','Órgano de Compliance designado e independiente','Formación periódica en compliance']),'obligatoria':False,'plazo':'MUY RECOMENDABLE — eximente o atenuante responsabilidad penal','sancion_min':0,'sancion_max':0,'sancion_desc':'Sin sanción por no tenerlo, pero su ausencia impide invocar exención de responsabilidad penal (art. 31 bis.2 CP).','orden_prioridad':10},
    {'codigo':'BLANQUEO','nombre':'Prevención de Blanqueo de Capitales y Financiación del Terrorismo','categoria':'compliance','normativa':'Ley 10/2010, de 28 de abril · RD 304/2014 · Directiva UE 2018/843','items_json':json.dumps(['Manual Interno de Prevención de Blanqueo (MIPBC)','Diligencia debida en identificación del cliente (KYC)','Declaración de operaciones sospechosas al SEPBLAC','Formación anual del personal en PBC/FT','Órgano de control interno (representante ante SEPBLAC)','Conservación documentación 10 años (art. 25 Ley 10/2010)']),'obligatoria':True,'plazo':'INMEDIATO para sujetos obligados','sancion_min':0,'sancion_max':10000000,'sancion_desc':'Muy graves: hasta 10.000.000€ o 10% facturación anual. Graves: hasta 5.000.000€.','orden_prioridad':11},
    {'codigo':'APPCC','nombre':'Plan APPCC + Registro Sanitario','categoria':'sanitario','normativa':'Reglamento CE 852/2004 · RD 191/2011 · Normativa autonómica alimentaria','items_json':json.dumps(['Plan APPCC específico de la actividad','Registro Sanitario o inscripción en Registro Autonómico','Formación de manipuladores de alimentos (acreditada)','Plan de Limpieza y Desinfección (L+D) documentado','Control y homologación de proveedores alimentarios','Sistema de Trazabilidad (art. 18 Reg. CE 178/2002)']),'obligatoria':True,'plazo':'Antes de iniciar la actividad alimentaria','sancion_min':300,'sancion_max':600000,'sancion_desc':'Ley 17/2011: leves 100€–3.000€, graves 3.001€–120.000€, muy graves 120.001€–600.000€. Posible cierre.','orden_prioridad':12},
]

def seed_catalogo():
    creados = 0
    for datos in CATALOGO:
        if not CatalogoObligacion.query.filter_by(codigo=datos['codigo']).first():
            db.session.add(CatalogoObligacion(**datos))
            creados += 1
    db.session.commit()
    if creados:
        print(f'[compliance] {creados} obligaciones añadidas al catálogo.')

def analizar_obligaciones(cliente):
    from models import Cliente
    catalogo_all = {c.codigo: c for c in CatalogoObligacion.query.filter_by(activa=True).all()}
    existentes = {oc.catalogo.codigo: oc for oc in ObligacionCliente.query.filter_by(cliente_id=cliente.id).all()}
    REGLAS = {
        'RGPD': lambda c: any([getattr(c,'num_empleados',0) and c.num_empleados>=1, getattr(c,'trata_datos_personales',False), getattr(c,'tiene_web',False), getattr(c,'tiene_rrss',False)]),
        'PRL': lambda c: getattr(c,'num_empleados',0) and c.num_empleados>=1,
        'REG_HORARIO': lambda c: getattr(c,'num_empleados',0) and c.num_empleados>=1,
        'REG_SALARIAL': lambda c: getattr(c,'num_empleados',0) and c.num_empleados>=1,
        'PLAN_IGUALDAD': lambda c: getattr(c,'num_empleados',0) and c.num_empleados>=50,
        'CANAL_DENUNCIAS': lambda c: getattr(c,'num_empleados',0) and c.num_empleados>=50,
        'LIC_APERTURA': lambda c: getattr(c,'tiene_local',False),
        'SEG_RC': lambda c: getattr(c,'tipo_sociedad','') in ('sl','sa','cooperativa') or (getattr(c,'num_empleados',0) and c.num_empleados>=1) or getattr(c,'tiene_local',False),
        'SEG_CONVENIO': lambda c: getattr(c,'num_empleados',0) and c.num_empleados>=1 and bool(getattr(c,'convenio_aplicable',None)),
        'COMPLIANCE_PENAL': lambda c: getattr(c,'tipo_sociedad','') in ('sl','sa') and ((getattr(c,'num_empleados',0) and c.num_empleados>=10) or (getattr(c,'facturacion_estimada',0) or 0)>2000000),
        'BLANQUEO': lambda c: getattr(c,'sector_obligado_blanqueo',False) or getattr(c,'opera_efectivo','no') in ('regular','ocasional'),
        'APPCC': lambda c: getattr(c,'manipula_alimentos',False),
    }
    for codigo, cat_obj in catalogo_all.items():
        aplica = REGLAS.get(codigo, lambda c: False)(cliente)
        oc = existentes.get(codigo)
        if aplica and not oc:
            items = cat_obj.get_items()
            oc = ObligacionCliente(
                cliente_id=cliente.id,
                catalogo_id=cat_obj.id,
                estado='pendiente',
                porcentaje_cumplimiento=0,
                items_estado_json=json.dumps({item:'pendiente' for item in items}, ensure_ascii=False),
                incluir_en_email=True,
            )
            db.session.add(oc)
        elif not aplica and oc and oc.estado == 'pendiente':
            oc.estado = 'no_aplica'
    db.session.flush()
    recalcular_compliance(cliente)
    db.session.commit()

def recalcular_compliance(cliente):
    obligaciones = ObligacionCliente.query.filter_by(cliente_id=cliente.id).filter(ObligacionCliente.estado != 'no_aplica').all()
    if not obligaciones:
        cliente.compliance_porcentaje = 0
        cliente.nivel_riesgo_compliance = 'sin_datos'
        return
    promedio = sum(oc.calcular_porcentaje() for oc in obligaciones) / len(obligaciones)
    cliente.compliance_porcentaje = int(promedio)
    cliente.ultimo_analisis_compliance = datetime.now()
    if promedio >= 90: cliente.nivel_riesgo_compliance = 'bajo'
    elif promedio >= 60: cliente.nivel_riesgo_compliance = 'medio'
    elif promedio >= 30: cliente.nivel_riesgo_compliance = 'alto'
    else: cliente.nivel_riesgo_compliance = 'critico'
