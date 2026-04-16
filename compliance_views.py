"""Rutas: compliance por cliente, alertas admin."""
from datetime import datetime
from decimal import Decimal
import json
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from sqlalchemy import case

from models import db, Cliente, CatalogoObligaciones, ObligacionClienteLegacy, AlertaCompliance, Trabajador
from compliance_service import (
    analizar_obligaciones_cliente_completo,
    finalizar_onboarding_completo,
    generar_email_compliance,
    generar_informe_compliance,
    recalcular_compliance_cliente,
    resolve_usuario_id_from_session,
    revisar_clientes_antiguos,
    revisar_vencimientos,
)

compliance_bp = Blueprint('compliance', __name__)

# Alias para reutilizar decorador sin importar app.py (evita circular imports).
login_required = None


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def _parse_float(s, default=0.0):
    if s is None or s == '':
        return default
    try:
        return float(str(s).replace(',', '.'))
    except ValueError:
        return default


def _parse_int(s, default=0):
    if s is None or s == '':
        return default
    try:
        return int(s)
    except ValueError:
        return default


def _remitente_desde_sesion():
    nombre = session.get('username') or 'Gestoría'
    email = ''
    tid = session.get('trabajador_id')
    if tid:
        t = Trabajador.query.get(tid)
        if t and t.email:
            email = t.email
    return {'nombre': nombre, 'email': email, 'cargo': 'Gestor', 'telefono': ''}


def guardar_paso_onboarding(cliente: Cliente, paso: int, form) -> None:
    if paso == 1:
        cliente.nombre = (form.get('nombre') or '').strip() or cliente.nombre
        cliente.razon_social = form.get('razon_social')
        cliente.nombre_comercial = form.get('nombre_comercial')
        cliente.cif = form.get('cif')
        cliente.tipo_sociedad = form.get('tipo_sociedad')
        cliente.fecha_constitucion = _parse_date(form.get('fecha_constitucion'))
        cliente.capital_social = _parse_float(form.get('capital_social'))
        cliente.direccion_fiscal = form.get('direccion_fiscal')
        cliente.codigo_postal = form.get('codigo_postal')
        cliente.municipio = form.get('municipio')
        cliente.provincia = form.get('provincia')
        cliente.pais = form.get('pais') or 'España'
        cliente.persona_contacto = form.get('persona_contacto')
        cliente.cargo_contacto = form.get('cargo_contacto')
        cliente.telefono_contacto = form.get('telefono_contacto')
        cliente.email_contacto = form.get('email_contacto')
        cliente.telefono = form.get('telefono')
        cliente.email = form.get('email')
        cliente.onboarding_paso_actual = 2
        cliente.onboarding_porcentaje = 17
    elif paso == 2:
        cliente.cnae_principal = form.get('cnae_principal')
        cliente.cnae_descripcion = form.get('cnae_descripcion')
        cliente.descripcion_actividad = form.get('descripcion_actividad')
        cliente.sector = form.get('sector')
        cliente.tiene_empleados = form.get('tiene_empleados') == 'si'
        cliente.num_empleados_actual = _parse_int(form.get('num_empleados_actual'))
        cliente.prevision_contratacion = form.get('prevision_contratacion') == 'si'
        cliente.prevision_num_empleados = _parse_int(form.get('prevision_num_empleados'))
        pps = form.get('prevision_plazo_meses')
        cliente.prevision_plazo_meses = int(pps) if pps and str(pps).isdigit() else None
        cliente.empleados_oficina = 'empleados_oficina' in form
        cliente.empleados_teletrabajo = 'empleados_teletrabajo' in form
        cliente.empleados_obra = 'empleados_obra' in form
        cliente.empleados_vehiculos = 'empleados_vehiculos' in form
        cliente.empleados_turnos = 'empleados_turnos' in form
        cliente.empleados_nocturnos = 'empleados_nocturnos' in form
        cliente.convenio_aplicable = form.get('convenio_aplicable')
        cliente.convenio_codigo = form.get('convenio_codigo')
        cliente.onboarding_paso_actual = 3
        cliente.onboarding_porcentaje = 34
    elif paso == 3:
        cliente.facturacion_anual = form.get('facturacion_anual')
        cliente.facturacion_estimada = _parse_float(form.get('facturacion_estimada'))
        cliente.opera_efectivo = form.get('opera_efectivo')
        cliente.volumen_efectivo_anual = _parse_float(form.get('volumen_efectivo_anual'))
        cliente.iban = form.get('iban')
        cliente.titular_cuenta = form.get('titular_cuenta')
        cliente.banco = form.get('banco')
        cliente.forma_pago = form.get('forma_pago')
        cliente.dia_facturacion = _parse_int(form.get('dia_facturacion'), 1) or 1
        dv = form.get('dia_vencimiento')
        cliente.dia_vencimiento = int(dv) if dv and str(dv).isdigit() else None
        cm = _parse_float(form.get('cuota_mensual_base'))
        cliente.precio_cuota_mensual = Decimal(str(cm))
        cliente.cuota_mensual = Decimal(str(cm))
        cliente.onboarding_paso_actual = 4
        cliente.onboarding_porcentaje = 51
    elif paso == 4:
        cliente.tiene_local = form.get('tiene_local') == 'si'
        if cliente.tiene_local:
            cliente.direccion_local = form.get('direccion_local')
            cliente.tipo_local = form.get('tipo_local')
            cliente.superficie_m2 = _parse_float(form.get('superficie_m2'))
            cliente.num_locales = _parse_int(form.get('num_locales'), 1)
            cliente.tiene_almacen = 'tiene_almacen' in form
            cliente.almacena_quimicos = 'almacena_quimicos' in form
            cliente.tiene_maquinaria = 'tiene_maquinaria' in form
            cliente.manipula_alimentos = 'manipula_alimentos' in form
            cliente.tiene_climatizacion = 'tiene_climatizacion' in form
            cliente.potencia_climatizacion_kw = _parse_float(form.get('potencia_climatizacion_kw'))
            cliente.tiene_ascensor = 'tiene_ascensor' in form
            cliente.tiene_parking = 'tiene_parking' in form
        cliente.onboarding_paso_actual = 5
        cliente.onboarding_porcentaje = 68
    elif paso == 5:
        cliente.tiene_web = form.get('tiene_web') == 'si'
        cliente.url_web = form.get('url_web') if cliente.tiene_web else None
        cliente.tiene_rrss = form.get('tiene_rrss') == 'si'
        if cliente.tiene_rrss:
            rr = form.getlist('rrss_activas')
            cliente.rrss_activas = json.dumps(rr, ensure_ascii=False)
        else:
            cliente.rrss_activas = None
        cliente.tiene_ecommerce = form.get('tiene_ecommerce') == 'si'
        cliente.plataforma_ecommerce = form.get('plataforma_ecommerce')
        cliente.trata_datos_personales = form.get('trata_datos_personales') == 'si'
        if cliente.trata_datos_personales:
            cliente.volumen_datos = form.get('volumen_datos')
            cliente.trata_datos_contacto = 'trata_datos_contacto' in form
            cliente.trata_datos_economicos = 'trata_datos_economicos' in form
            cliente.trata_datos_salud = 'trata_datos_salud' in form
            cliente.trata_datos_menores = 'trata_datos_menores' in form
            cliente.trata_datos_biometricos = 'trata_datos_biometricos' in form
            cliente.trata_datos_judicial = 'trata_datos_judicial' in form
        cliente.onboarding_paso_actual = 6
        cliente.onboarding_porcentaje = 85
    elif paso == 6:
        cliente.observaciones_comerciales = form.get('observaciones_onboarding')
        cliente.onboarding_porcentaje = 95
    db.session.commit()


def login_required_wrap(f):
    from functools import wraps
    from flask import session as sess

    @wraps(f)
    def inner(*a, **kw):
        if 'user_id' not in sess:
            return redirect(url_for('login'))
        return f(*a, **kw)

    return inner


# Usar el decorador local como `login_required` para las rutas nuevas pedidas.
login_required = login_required_wrap


def _get_or_create_cuestionario(cliente: Cliente):
    from models import CuestionarioNormativoCliente
    from cuestionario_normativo_data import ids as cuestionario_ids
    rec = CuestionarioNormativoCliente.query.filter_by(cliente_id=cliente.id).first()
    if not rec:
        rec = CuestionarioNormativoCliente(cliente_id=cliente.id, respuestas_json='{}')
        db.session.add(rec)
        db.session.flush()
    data = rec.get_respuestas()
    for iid in cuestionario_ids():
        data.setdefault(iid, '')
    rec.set_respuestas(data)
    db.session.commit()
    return rec


## Onboarding eliminado por requerimiento


def admin_required_wrap(f):
    from functools import wraps
    from flask import session as sess, flash as fl, redirect as redir

    @wraps(f)
    def inner(*a, **kw):
        if 'user_id' not in sess:
            return redir(url_for('login'))
        if sess.get('rol') != 'ADMIN':
            fl('Se requieren permisos de administrador.', 'error')
            return redir(url_for('dashboard'))
        return f(*a, **kw)

    return inner


@compliance_bp.route('/clientes/nuevo/onboarding', methods=['GET', 'POST'])
@login_required_wrap
def cliente_onboarding_wizard():
    flash('Onboarding eliminado por requerimiento.', 'info')
    return redirect(url_for('clientes'))


@compliance_bp.route('/clientes/<int:id>/compliance-legacy')
@login_required_wrap
def ver_cliente_compliance(id):
    cliente = Cliente.query.get_or_404(id)
    obligaciones = (
        ObligacionClienteLegacy.query.filter_by(cliente_id=id)
        .join(CatalogoObligaciones)
        .order_by(CatalogoObligaciones.orden_prioridad)
        .all()
    )
    total = len(obligaciones)
    cumplidas = len([o for o in obligaciones if o.estado == 'cumplido'])
    pendientes = len([o for o in obligaciones if o.estado == 'pendiente'])
    en_proceso = len([o for o in obligaciones if o.estado == 'en_proceso'])
    porcentaje = (cumplidas / total * 100) if total else 0
    return render_template(
        'compliance/cliente_compliance.html',
        cliente=cliente,
        obligaciones=obligaciones,
        total=total,
        cumplidas=cumplidas,
        pendientes=pendientes,
        en_proceso=en_proceso,
        porcentaje=porcentaje,
    )


@compliance_bp.route('/clientes/<int:id>/compliance/obligacion/<int:oblig_id>/actualizar', methods=['POST'])
@login_required_wrap
def actualizar_estado_obligacion(id, oblig_id):
    oblig = ObligacionClienteLegacy.query.get_or_404(oblig_id)
    if oblig.cliente_id != id:
        abort(404)
    cat = oblig.catalogo
    items = cat.get_items()
    items_estado = oblig.get_items_estado()
    # Checklist: checkbox marcado => cumplido; sin marcar => pendiente
    for i, item in enumerate(items):
        key = f'item_{i}'
        items_estado[item] = 'cumplido' if request.form.get(key) == 'on' else 'pendiente'
    oblig.items_estado_json = json.dumps(items_estado, ensure_ascii=False)
    total_items = len(items_estado) or 1
    items_cumplidos = len([v for v in items_estado.values() if v == 'cumplido'])
    oblig.porcentaje_cumplimiento = int((items_cumplidos / total_items) * 100)
    if oblig.porcentaje_cumplimiento == 100:
        oblig.estado = 'cumplido'
        oblig.fecha_cumplimiento = datetime.utcnow()
    elif oblig.porcentaje_cumplimiento > 0:
        oblig.estado = 'en_proceso'
    else:
        oblig.estado = 'pendiente'
    oblig.incluir_en_email = request.form.get('incluir_en_email') == 'si'
    db.session.commit()
    recalcular_compliance_cliente(id)
    flash('Obligación actualizada.', 'success')
    return redirect(url_for('compliance.ver_cliente_compliance', id=id))


@compliance_bp.route('/clientes/<int:id>/compliance/generar-checklist', methods=['POST'])
@login_required_wrap
def generar_checklist_cliente(id):
    """Genera (si faltan) obligaciones aplicables según el catálogo y datos actuales."""
    cliente = Cliente.query.get_or_404(id)
    analizar_obligaciones_cliente_completo(cliente)
    db.session.commit()
    recalcular_compliance_cliente(cliente.id)
    flash('Checklist generada/actualizada según los datos actuales del cliente.', 'success')
    return redirect(url_for('compliance.ver_cliente_compliance', id=id))


@compliance_bp.route('/clientes/<int:id>/onboarding', methods=['GET'])
@login_required_wrap
def cliente_onboarding_existente(id):
    flash('Onboarding eliminado por requerimiento.', 'info')
    return redirect(url_for('clientes'))


@compliance_bp.route('/clientes/<int:id>/compliance/generar-email', methods=['POST'])
@login_required_wrap
def generar_email_compliance_manual(id):
    cliente = Cliente.query.get_or_404(id)
    uid = resolve_usuario_id_from_session(session)
    informe = generar_informe_compliance(cliente, tipo='manual', usuario_id=uid)
    generar_email_compliance(cliente, informe, _remitente_desde_sesion())
    dest = cliente.email_contacto or cliente.email or '—'
    flash(f'Informe generado. Email al cliente: {dest} (envío real si configura COMPLIANCE_MAIL_ENABLED).', 'success')
    return redirect(url_for('compliance.ver_cliente_compliance', id=id))


## Subida de documentación deshabilitada por requerimiento (solo checklist).


@compliance_bp.route('/admin/alertas-compliance')
@admin_required_wrap
def ver_alertas_compliance():
    alertas = (
        AlertaCompliance.query.filter_by(estado='pendiente')
        .order_by(
            case(
                (AlertaCompliance.prioridad == 'urgente', 1),
                (AlertaCompliance.prioridad == 'alta', 2),
                (AlertaCompliance.prioridad == 'media', 3),
                else_=4,
            ),
            AlertaCompliance.fecha_vencimiento,
        )
        .all()
    )
    return render_template(
        'compliance/alertas_admin.html',
        alertas=alertas,
        total_alertas=len(alertas),
        urgentes=len([a for a in alertas if a.prioridad == 'urgente']),
        altas=len([a for a in alertas if a.prioridad == 'alta']),
    )


@compliance_bp.route('/admin/alertas-compliance/<int:aid>/resolver', methods=['POST'])
@admin_required_wrap
def resolver_alerta_compliance(aid):
    alerta = AlertaCompliance.query.get_or_404(aid)
    alerta.estado = 'resuelta'
    alerta.fecha_resolucion = datetime.utcnow()
    alerta.resuelto_por_id = resolve_usuario_id_from_session(session)
    alerta.observaciones_resolucion = request.form.get('observaciones')
    db.session.commit()
    flash('Alerta cerrada.', 'success')
    return redirect(url_for('compliance.ver_alertas_compliance'))


@compliance_bp.route('/admin/alertas-compliance/<int:aid>/revisar-cliente', methods=['POST'])
@admin_required_wrap
def revisar_cliente_desde_alerta(aid):
    alerta = AlertaCompliance.query.get_or_404(aid)
    alerta.estado = 'en_revision'
    alerta.asignado_a_id = resolve_usuario_id_from_session(session)
    db.session.commit()
    return redirect(url_for('compliance.ver_cliente_compliance', id=alerta.cliente_id))


@compliance_bp.route('/admin/compliance/ejecutar-revision', methods=['POST'])
@admin_required_wrap
def ejecutar_revision_compliance_manual():
    n1 = revisar_clientes_antiguos()
    n2 = revisar_vencimientos()
    flash(f'Revisión ejecutada: {n1} alertas por antigüedad, {n2} por vencimientos.', 'success')
    return redirect(url_for('compliance.ver_alertas_compliance'))


# ==================== RUTAS NUEVAS (compliance_engine.py) ====================

@compliance_bp.route('/clientes/<int:cliente_id>/compliance', methods=['GET', 'POST'])
@login_required
def ver_compliance(cliente_id):
    """Pestaña Compliance: cuestionario SI/NO/PTE."""
    from cuestionario_normativo_data import CUESTIONARIO
    cliente = Cliente.query.get_or_404(cliente_id)
    rec = _get_or_create_cuestionario(cliente)
    respuestas = rec.get_respuestas()

    if request.method == 'POST':
        for row in CUESTIONARIO:
            iid = row['id']
            v = request.form.get(f"r__{iid}", '')
            if v in ('SI', 'NO', 'PTE', ''):
                respuestas[iid] = v
        rec.set_respuestas(respuestas)
        db.session.commit()
        flash('Cuestionario guardado.', 'success')
        return redirect(url_for('compliance.ver_compliance', cliente_id=cliente.id))

    pendientes = [r for r in CUESTIONARIO if respuestas.get(r['id'], '') in ('', 'PTE')]
    return render_template(
        'compliance/cuestionario_normativo.html',
        cliente=cliente,
        cuestionario=CUESTIONARIO,
        respuestas=respuestas,
        pendientes_total=len(pendientes),
    )

@compliance_bp.route('/clientes/<int:cliente_id>/compliance-engine-legacy')
@login_required
def ver_compliance_engine_legacy(cliente_id):
    """Vista legacy del motor antiguo (se conserva, pero se saca del endpoint principal)."""
    from models import Cliente
    from compliance_engine import ObligacionCliente, CatalogoObligacion, SolicitudPresupuesto
    cliente = Cliente.query.get_or_404(cliente_id)
    obligaciones = ObligacionCliente.query.filter_by(cliente_id=cliente_id).join(CatalogoObligacion).order_by(CatalogoObligacion.orden_prioridad).all()
    categorias = {}
    for oc in obligaciones:
        cat = oc.catalogo.categoria
        categorias.setdefault(cat, []).append(oc)
    total = len([o for o in obligaciones if o.estado != 'no_aplica'])
    cumplidas = len([o for o in obligaciones if o.estado == 'cumplido'])
    pendientes = len([o for o in obligaciones if o.estado == 'pendiente'])
    en_proceso = len([o for o in obligaciones if o.estado == 'en_proceso'])
    codigos_solicitados = {s.catalogo.codigo for s in SolicitudPresupuesto.query.filter_by(cliente_id=cliente_id).filter(SolicitudPresupuesto.estado.notin_(['rechazado','cerrado'])).all()}
    return render_template('compliance/cliente_compliance.html', cliente=cliente, obligaciones=obligaciones, categorias=categorias, total=total, cumplidas=cumplidas, pendientes=pendientes, en_proceso=en_proceso, codigos_solicitados=codigos_solicitados)

@compliance_bp.route('/clientes/<int:cliente_id>/compliance/<int:oc_id>/actualizar', methods=['POST'])
@login_required
def actualizar_obligacion(cliente_id, oc_id):
    from models import db
    from compliance_engine import ObligacionCliente, recalcular_compliance
    import json
    oc = ObligacionCliente.query.get_or_404(oc_id)
    f = request.form
    items_estado = oc.get_items_estado()
    for item in items_estado:
        key = 'item__' + item.replace(' ','_').replace('(','').replace(')','').replace('/','_')
        nuevo = f.get(key)
        if nuevo in ('pendiente','en_proceso','cumplido'):
            items_estado[item] = nuevo
    oc.items_estado_json = json.dumps(items_estado, ensure_ascii=False)
    oc.porcentaje_cumplimiento = oc.calcular_porcentaje()
    pct = oc.porcentaje_cumplimiento
    if pct == 100:
        oc.estado = 'cumplido'
        if not oc.fecha_cumplimiento:
            from datetime import datetime
            oc.fecha_cumplimiento = datetime.now()
    elif pct > 0:
        oc.estado = 'en_proceso'
    else:
        oc.estado = 'pendiente'
    oc.incluir_en_email = f.get('incluir_en_email') == 'si'
    oc.observaciones = f.get('observaciones','').strip() or None
    db.session.commit()
    recalcular_compliance(oc.cliente)
    db.session.commit()
    flash('Obligación actualizada.', 'success')
    return redirect(url_for('compliance.ver_compliance', cliente_id=cliente_id))

@compliance_bp.route('/clientes/<int:cliente_id>/compliance/<int:oc_id>/solicitar-presupuesto', methods=['POST'])
@login_required
def solicitar_presupuesto(cliente_id, oc_id):
    from models import db, Cliente
    from compliance_engine import ObligacionCliente, SolicitudPresupuesto
    from datetime import datetime
    oc = ObligacionCliente.query.get_or_404(oc_id)
    cliente = Cliente.query.get_or_404(cliente_id)
    existente = SolicitudPresupuesto.query.filter_by(cliente_id=cliente_id, catalogo_id=oc.catalogo_id).filter(SolicitudPresupuesto.estado.notin_(['rechazado','cerrado'])).first()
    if existente:
        flash('Ya hay una solicitud activa para esta obligación.', 'warning')
        return redirect(url_for('compliance.ver_compliance', cliente_id=cliente_id))
    sol = SolicitudPresupuesto(cliente_id=cliente_id, obligacion_id=oc_id, catalogo_id=oc.catalogo_id, notas_internas=request.form.get('notas','').strip() or None)
    db.session.add(sol)
    db.session.commit()
    # Email interno
    try:
        from flask_mail import Mail, Message
        mail = Mail(current_app)
        dest = current_app.config.get('MAIL_DESPACHO_ADDR') or current_app.config.get('MAIL_USERNAME','')
        if dest:
            msg = Message(f'[Presupuesto] {oc.catalogo.nombre} — {cliente.nombre}', recipients=[dest])
            msg.html = f'<h3>Nueva solicitud de presupuesto</h3><p><b>Cliente:</b> {cliente.nombre}<br><b>Obligación:</b> {oc.catalogo.nombre}<br><b>Normativa:</b> {oc.catalogo.normativa}</p>'
            mail.send(msg)
    except Exception as e:
        current_app.logger.warning(f'Email presupuesto no enviado: {e}')
    flash(f'Presupuesto solicitado para {oc.catalogo.nombre}.', 'success')
    return redirect(url_for('compliance.ver_compliance', cliente_id=cliente_id))

@compliance_bp.route('/admin/presupuestos')
@login_required
def dashboard_presupuestos():
    from compliance_engine import SolicitudPresupuesto, CatalogoObligacion
    from models import Cliente
    estado_filtro = request.args.get('estado','')
    q = SolicitudPresupuesto.query.join(CatalogoObligacion)
    if estado_filtro:
        q = q.filter(SolicitudPresupuesto.estado == estado_filtro)
    solicitudes = q.order_by(SolicitudPresupuesto.fecha_solicitud.desc()).all()
    contadores = {e: SolicitudPresupuesto.query.filter_by(estado=e).count() for e in ['solicitado','en_preparacion','enviado','aceptado','rechazado']}
    return render_template('presupuestos/dashboard.html', solicitudes=solicitudes, contadores=contadores, estado_filtro=estado_filtro)

@compliance_bp.route('/admin/presupuestos/<int:sol_id>', methods=['GET','POST'])
@login_required
def detalle_presupuesto(sol_id):
    from compliance_engine import SolicitudPresupuesto
    from models import db
    from datetime import datetime
    sol = SolicitudPresupuesto.query.get_or_404(sol_id)
    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'cambiar_estado':
            nuevo = request.form.get('nuevo_estado')
            if nuevo in ('solicitado','en_preparacion','enviado','aceptado','rechazado','cerrado'):
                sol.estado = nuevo
                if nuevo == 'enviado': sol.fecha_envio_presupuesto = datetime.now()
                elif nuevo in ('aceptado','rechazado'): sol.fecha_respuesta = datetime.now()
        elif accion == 'registrar_importe':
            try: sol.importe_propuesto = float(request.form.get('importe_propuesto',0))
            except: pass
            sol.notas_internas = request.form.get('notas_internas','').strip() or None
        elif accion == 'enviar_cliente':
            try:
                from flask_mail import Mail, Message
                mail = Mail(current_app)
                dest = sol.cliente.email or ''
                if dest:
                    msg = Message(f'Presupuesto — {sol.catalogo.nombre}', recipients=[dest])
                    msg.html = f'<h3>Presupuesto</h3><p><b>Servicio:</b> {sol.catalogo.nombre}<br><b>Importe:</b> {sol.importe_propuesto or "A determinar"} €</p>'
                    mail.send(msg)
                    sol.estado = 'enviado'
                    sol.fecha_envio_presupuesto = datetime.now()
                    flash('Email enviado al cliente.', 'success')
            except Exception as e:
                flash(f'Error al enviar email: {e}', 'danger')
        db.session.commit()
        flash('Solicitud actualizada.', 'success')
        return redirect(url_for('compliance.detalle_presupuesto', sol_id=sol_id))
    return render_template('presupuestos/detalle.html', sol=sol)

@compliance_bp.route('/clientes/<int:cliente_id>/compliance/recalcular', methods=['POST'])
@login_required
def recalcular_compliance_manual(cliente_id):
    from models import Cliente
    from compliance_engine import analizar_obligaciones
    cliente = Cliente.query.get_or_404(cliente_id)
    analizar_obligaciones(cliente)
    flash('Compliance recalculado.', 'success')
    return redirect(url_for('compliance.ver_compliance', cliente_id=cliente_id))
