"""
Cuestionario de cumplimiento normativo (Agencia de Viajes Online · Ceuta).
Normativa vigente a abril 2025 (según PDF aportado).

Estados esperados por punto:
- SI
- NO
- PTE
- '' (sin marcar)
"""

CUESTIONARIO = [
    {
        "id": "dni_nif_titular",
        "campo": "DNI / NIF del titular o administrador",
        "descripcion": "Documento Nacional de Identidad vigente del titular o del representante legal de la empresa. Debe estar en vigor y coincidir con el firmante de los contratos, licencias y declaraciones fiscales ante todos los organismos.",
    },
    {
        "id": "escritura_constitucion",
        "campo": "Escritura de constitución",
        "descripcion": "Si la empresa se constituye como Sociedad Limitada: escritura notarial de constitución con inscripción en el Registro Mercantil. Si opera como autónomo: alta censal mediante modelo 036/037 ante la AEAT. Es el documento que acredita la existencia legal de la empresa.",
    },
    {
        "id": "certificado_digital",
        "campo": "Certificado digital",
        "descripcion": "Certificado electrónico reconocido emitido por la FNMT-RCM (persona física o jurídica). Imprescindible para realizar trámites telemáticos ante la AEAT, la Seguridad Social, la sede electrónica de la Ciudad Autónoma de Ceuta y el OASTCE (organismo tributario local de Ceuta).",
    },
    {"id": "alta_dehu", "campo": "Alta en DeHU", "descripcion": ""},
    {"id": "gestiona_is_notificaciones", "campo": "Gestiona IS Notificaciones", "descripcion": ""},
    {"id": "gestiona_cliente_notificaciones", "campo": "Gestiona Cliente Notificaciones", "descripcion": ""},
    {
        "id": "telefono_contacto",
        "campo": "Teléfono de contacto",
        "descripcion": "Número de teléfono de la empresa o del titular. Debe figurar en la web, en la documentación presentada ante los organismos competentes y en el alta censal. Puede ser fijo o móvil.",
    },
    {"id": "correo_electronico", "campo": "Correo Electrónico", "descripcion": ""},
    {
        "id": "domicilio_fiscal_ceuta",
        "campo": "Dirección / domicilio fiscal en Ceuta",
        "descripcion": "El domicilio social y fiscal debe estar obligatoriamente ubicado en la Ciudad Autónoma de Ceuta para poder acogerse al régimen fiscal especial del IPSI y tramitar la licencia local. Puede ser un local comercial, despacho o domicilio particular habilitado como sede de actividad.",
    },
    {
        "id": "cuenta_bancaria",
        "campo": "Número de cuenta bancaria",
        "descripcion": "Cuenta corriente titularidad de la empresa o del autónomo en una entidad financiera autorizada. Necesaria para la domiciliación de impuestos (AEAT y OASTCE), el pago de cuotas a la Seguridad Social, el cobro de clientes online y la gestión de avales o garantías. Se recomienda mantener una cuenta separada de la personal.",
    },
    {
        "id": "licencia_apertura",
        "campo": "Licencia de apertura o declaración responsable",
        "descripcion": "Trámite ante el Ayuntamiento de Ceuta (Negociado de Licencias, Sección de Urbanismo y Actividades). Para una agencia de viajes online sin atención presencial al público, en la mayoría de los casos es suficiente con presentar una declaración responsable o comunicación previa de inicio de actividad, sin necesidad de licencia de obras ni de acondicionamiento del local.",
    },
    {
        "id": "alta_iae_036",
        "campo": "Alta censal en IAE (modelo 036 - epígrafe 755.2)",
        "descripcion": "Alta en el Impuesto sobre Actividades Económicas mediante el modelo 036 de declaración censal ante la AEAT, indicando el epígrafe 755.2: 'Servicios prestados al público por las agencias de viajes'. Las empresas de nueva creación con facturación previsible inferior a 1.000.000 euros anuales están exentas del pago del IAE durante los primeros ejercicios.",
    },
    {
        "id": "seguro_rc_profesional",
        "campo": "Seguro de responsabilidad civil profesional (min. 150.153 euros)",
        "descripcion": "Póliza de seguro que cubre los daños y perjuicios causados a clientes y terceros en el ejercicio de la actividad de intermediación turística y organización de viajes. La cobertura mínima legalmente exigida es de 150.153 euros. Debe contratarse antes del inicio de la actividad y mantenerse vigente de forma permanente. Su cancelación puede implicar la suspensión o revocación de la licencia.",
    },
    {
        "id": "seguro_local_sede",
        "campo": "Seguro del local / sede",
        "descripcion": "Póliza multirriesgo del hogar o del local comercial que cubre el espacio físico donde se desarrolla la actividad. Incluye habitualmente cobertura de daños materiales por incendio, robo, agua y responsabilidad civil del local. Si el espacio está arrendado, el contrato de arrendamiento suele exigir al arrendatario la contratación de este seguro.",
    },
    {
        "id": "seguro_convenio",
        "campo": "Seguro de convenio colectivo",
        "descripcion": "El Convenio Colectivo estatal de agencias de viajes establece la obligación de contratar un seguro de accidentes colectivo para los trabajadores. Al no tener empleados en el momento del inicio de la actividad, este seguro no resulta obligatorio. Deberá contratarse en el momento en que se produzca la primera contratación laboral.",
    },
    {
        "id": "alta_ipsi_001",
        "campo": "Alta en el IPSI - Modelo 001 (Ceuta)",
        "descripcion": "El Impuesto sobre la Producción, los Servicios y la Importación (IPSI) sustituye al IVA en Ceuta. Alta mediante Modelo 001 ante OASTCE. Tipo general 10%. Liquidación trimestral: 30 enero, 20 abril, 20 julio y 20 octubre.",
    },
    {
        "id": "ipsi_exencion",
        "campo": "Solicitud de exención del IPSI",
        "descripcion": "Las empresas de nueva creación o de bajo volumen pueden solicitar ante el OASTCE la exención total o parcial del IPSI durante los primeros ejercicios. Se recomienda solicitarla en el mismo momento del alta.",
    },
    {
        "id": "ipsi_fraccionamiento_3m",
        "campo": "Solicitud de fraccionamiento a 3 meses",
        "descripcion": "Posibilidad de fraccionar el pago trimestral del IPSI en tres mensualidades. La solicitud se presenta ante el OASTCE con justificación económica. Puede requerirse aval/garantía según umbrales.",
    },
    {
        "id": "ipsi_aplazamiento_2a",
        "campo": "Solicitud de aplazamiento a 2 años",
        "descripcion": "Aplazamiento extraordinario hasta 24 meses. Requiere motivación acreditada y, habitualmente, aval o garantía ante el OASTCE.",
    },
    {
        "id": "alta_iva",
        "campo": "Alta en el IVA",
        "descripcion": "Con domicilio fiscal en Ceuta no están sujetos a IVA por operaciones en territorio ceutí. El IVA se sustituye por IPSI. Solo aplica IVA en operaciones puntuales con Península o Baleares según la 'regla de cierre'.",
    },
    {
        "id": "prl_lprl",
        "campo": "Prevención de Riesgos Laborales (LPRL)",
        "descripcion": "Obligaciones como empleador solo cuando hay trabajadores. Sin empleados no aplica al inicio. Se recomienda una evaluación básica de riesgos del puesto del autónomo.",
    },
    {
        "id": "registro_jornada",
        "campo": "Registro de jornada",
        "descripcion": "Obligación del empleador respecto de trabajadores. Sin empleados no aplica. Debe implantarse desde la primera contratación, conservando los registros durante un mínimo de cuatro años.",
    },
    {
        "id": "registro_retributivo",
        "campo": "Registro retributivo",
        "descripcion": "Empresas con trabajadores deben disponer de un registro de valores medios salariales desagregados por sexo y categoría profesional. Sin empleados no aplica; debe elaborarse desde la primera contratación.",
    },
    {
        "id": "rgpd",
        "campo": "LOPD / RGPD - Protección de datos",
        "descripcion": "Desde el primer día debe cumplirse RGPD/LOPDGDD: RAT, política de privacidad, contratos con encargados y notificación de brechas a la AEPD en 72 horas.",
    },
    {
        "id": "lssi",
        "campo": "Cumplimiento LSSI - Comercio electrónico",
        "descripcion": "Operar por internet exige LSSI: Aviso Legal, condiciones de contratación, política de cookies (AEPD) y pagos seguros con SSL/TLS.",
    },
    {
        "id": "blanqueo",
        "campo": "Prevención del blanqueo de capitales",
        "descripcion": "Agencias de viajes no figuran en el listado de sujetos obligados del art. 2 Ley 10/2010. No están obligadas a diligencia debida ni a comunicar al SEPBLAC. Puede cambiar si la empresa realiza operaciones financieras habituales de gran volumen.",
    },
]


def ids():
    return [x["id"] for x in CUESTIONARIO]

