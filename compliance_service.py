"""Lógica de evaluación de obligaciones, onboarding y compliance."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, date

from flask import render_template, current_app

from models import (
    db,
    Cliente,
    CatalogoObligaciones,
    ObligacionCliente,
    InformeCompliance,
    AlertaCompliance,
    Usuario,
)


def _attr(cliente: Cliente, campo: str):
    return getattr(cliente, campo, None)


def evaluar_condicion_recursiva(cliente: Cliente, condicion) -> bool:
    if isinstance(condicion, dict):
        if 'AND' in condicion:
            return all(evaluar_condicion_recursiva(cliente, c) for c in condicion['AND'])
        if 'OR' in condicion:
            return any(evaluar_condicion_recursiva(cliente, c) for c in condicion['OR'])
        for campo, valor_esperado in condicion.items():
            if campo in ('AND', 'OR'):
                continue
            valor_cliente = _attr(cliente, campo)
            if isinstance(valor_esperado, dict):
                for op, v in valor_esperado.items():
                    if op == '>=':
                        vc = valor_cliente if valor_cliente is not None else 0
                        if isinstance(vc, bool):
                            vc = int(vc)
                        try:
                            if float(vc) < float(v):
                                return False
                        except (TypeError, ValueError):
                            return False
                    elif op == '>':
                        vc = valor_cliente if valor_cliente is not None else 0
                        try:
                            if float(vc) <= float(v):
                                return False
                        except (TypeError, ValueError):
                            return False
                    elif op == 'in':
                        if valor_cliente not in v:
                            return False
                    elif op == '!=':
                        if v is None:
                            if not valor_cliente or (
                                isinstance(valor_cliente, str) and not str(valor_cliente).strip()
                            ):
                                return False
                        elif valor_cliente == v:
                            return False
            else:
                if valor_cliente != valor_esperado:
                    return False
        return True
    return True


def evaluar_condiciones_obligacion(cliente: Cliente, obligacion: CatalogoObligaciones) -> bool:
    if not obligacion.condiciones_json:
        return True
    try:
        condiciones = json.loads(obligacion.condiciones_json)
    except (json.JSONDecodeError, TypeError):
        return True
    return evaluar_condicion_recursiva(cliente, condiciones)


def generar_documentos_onboarding(cliente: Cliente) -> None:
    """
    Conservado por compatibilidad (modelo existente), pero el flujo actual NO gestiona documentación.
    """
    return None


def analizar_obligaciones_cliente_completo(cliente: Cliente) -> None:
    existentes = {
        o.catalogo_id
        for o in ObligacionCliente.query.filter_by(cliente_id=cliente.id).all()
    }
    for obligacion in CatalogoObligaciones.query.filter_by(activa=True).all():
        if obligacion.id in existentes:
            continue
        if not evaluar_condiciones_obligacion(cliente, obligacion):
            continue
        items = obligacion.get_items()
        items_estado = {item: 'pendiente' for item in items}
        oc = ObligacionCliente(
            cliente_id=cliente.id,
            catalogo_id=obligacion.id,
            estado='pendiente',
            porcentaje_cumplimiento=0,
            incluir_en_email=True,
            items_estado_json=json.dumps(items_estado, ensure_ascii=False),
        )
        db.session.add(oc)


def recalcular_compliance_cliente(cliente_id: int) -> None:
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return
    obligaciones = ObligacionCliente.query.filter_by(cliente_id=cliente_id).all()
    if not obligaciones:
        cliente.compliance_porcentaje = 0
        cliente.nivel_riesgo_compliance = 'medio'
        db.session.commit()
        return
    prom = sum(o.porcentaje_cumplimiento or 0 for o in obligaciones) / len(obligaciones)
    cliente.compliance_porcentaje = int(prom)
    p = cliente.compliance_porcentaje
    if p >= 90:
        cliente.nivel_riesgo_compliance = 'bajo'
    elif p >= 50:
        cliente.nivel_riesgo_compliance = 'medio'
    elif p >= 25:
        cliente.nivel_riesgo_compliance = 'alto'
    else:
        cliente.nivel_riesgo_compliance = 'critico'
    db.session.commit()


def generar_informe_compliance(cliente: Cliente, tipo: str = 'inicial', usuario_id=None) -> InformeCompliance:
    todas = ObligacionCliente.query.filter_by(cliente_id=cliente.id).all()
    total = len(todas)
    cumplidas = len([o for o in todas if o.estado == 'cumplido'])
    pendientes = len([o for o in todas if o.estado == 'pendiente'])
    en_proceso = len([o for o in todas if o.estado == 'en_proceso'])
    no_aplican = len([o for o in todas if o.estado == 'no_aplica'])
    recalcular_compliance_cliente(cliente.id)
    cliente = Cliente.query.get(cliente.id)
    informe = InformeCompliance(
        cliente_id=cliente.id,
        tipo=tipo,
        total_obligaciones=total,
        obligaciones_cumplidas=cumplidas,
        obligaciones_pendientes=pendientes,
        obligaciones_en_proceso=en_proceso,
        obligaciones_no_aplican=no_aplican,
        porcentaje_cumplimiento=cliente.compliance_porcentaje,
        nivel_riesgo=cliente.nivel_riesgo_compliance,
        generado_por_id=usuario_id,
    )
    db.session.add(informe)
    db.session.commit()
    return informe


def generar_email_compliance(cliente: Cliente, informe: InformeCompliance, remitente: dict) -> None:
    obligaciones = (
        ObligacionCliente.query.filter_by(cliente_id=cliente.id, incluir_en_email=True)
        .join(CatalogoObligaciones)
        .filter(
            ObligacionCliente.estado != 'cumplido',
            ObligacionCliente.estado != 'no_aplica',
        )
        .order_by(CatalogoObligaciones.orden_prioridad)
        .all()
    )
    html = render_template(
        'emails/compliance_cliente.html',
        cliente=cliente,
        obligaciones=obligaciones,
        informe=informe,
        remitente=remitente,
    )
    informe.email_contenido = html
    informe.email_generado = True
    if enviar_email_compliance(cliente, html):
        informe.email_enviado = True
        informe.fecha_envio_email = datetime.utcnow()
    db.session.commit()


def enviar_email_compliance(cliente: Cliente, html_contenido: str) -> bool:
    """Integrar Flask-Mail u otro proveedor; por defecto no envía (solo guarda HTML)."""
    try:
        cfg = current_app.config.get('COMPLIANCE_MAIL_ENABLED')
        if not cfg:
            return False
        # Aquí: send_mail(...)
        return False
    except RuntimeError:
        return False


def finalizar_onboarding_completo(cliente: Cliente, usuario_id: int | None, remitente: dict) -> None:
    cliente.onboarding_completado = True
    cliente.onboarding_fecha_fin = datetime.utcnow()
    cliente.onboarding_porcentaje = 100
    analizar_obligaciones_cliente_completo(cliente)
    db.session.commit()
    recalcular_compliance_cliente(cliente.id)
    informe = generar_informe_compliance(cliente, tipo='inicial', usuario_id=usuario_id)
    generar_email_compliance(cliente, informe, remitente)
    cliente.ultimo_analisis_compliance = datetime.utcnow()
    db.session.commit()


def resolve_usuario_id_from_session(sess: dict) -> int | None:
    if sess.get('login_via') == 'trabajador' and sess.get('trabajador_id'):
        u = Usuario.query.filter_by(trabajador_id=sess['trabajador_id']).first()
        return u.id if u else None
    uid = sess.get('user_id')
    if uid and sess.get('login_via') == 'usuario':
        return uid
    return None


def revisar_clientes_antiguos() -> int:
    """Clientes activos sin análisis en 12 meses → alerta."""
    hace_12 = datetime.utcnow() - timedelta(days=365)
    q = Cliente.query.filter(
        Cliente.activo == True,  # noqa: E712
        db.or_(
            Cliente.ultimo_analisis_compliance.is_(None),
            Cliente.ultimo_analisis_compliance < hace_12,
        ),
    )
    creadas = 0
    for cliente in q.all():
        existe = AlertaCompliance.query.filter_by(
            cliente_id=cliente.id,
            tipo='revision_anual',
            estado='pendiente',
        ).first()
        if existe:
            continue
        ult = cliente.ultimo_analisis_compliance
        desc = (
            f'El cliente {cliente.nombre} no tiene análisis de compliance actualizado. '
            f'Última revisión: {ult.strftime("%d/%m/%Y") if ult else "Nunca"}.'
        )
        db.session.add(
            AlertaCompliance(
                cliente_id=cliente.id,
                tipo='revision_anual',
                prioridad='media',
                titulo=f'Revisión de compliance: {cliente.nombre}',
                descripcion=desc,
                fecha_vencimiento=datetime.utcnow() + timedelta(days=30),
            )
        )
        creadas += 1
    if creadas:
        db.session.commit()
    return creadas


def revisar_vencimientos() -> int:
    hoy = date.today()
    en_30 = hoy + timedelta(days=30)
    creadas = 0
    for doc in DocumentoOnboarding.query.filter(
        DocumentoOnboarding.fecha_vencimiento.isnot(None)
    ).all():
        fv = doc.fecha_vencimiento
        if fv is None:
            continue
        d = fv.date() if isinstance(fv, datetime) else fv
        if not (hoy <= d <= en_30):
            continue
        dias = (d - hoy).days
        prioridad = 'urgente' if dias <= 7 else 'alta' if dias <= 15 else 'media'
        db.session.add(
            AlertaCompliance(
                cliente_id=doc.cliente_id,
                tipo='vencimiento_documento',
                prioridad=prioridad,
                titulo=f'Vence {doc.nombre} — cliente #{doc.cliente_id}',
                descripcion=f'El documento "{doc.nombre}" vence el {d.strftime("%d/%m/%Y")} ({dias} días).',
                fecha_vencimiento=doc.fecha_vencimiento,
            )
        )
        creadas += 1
    for oblig in ObligacionCliente.query.filter(
        ObligacionCliente.fecha_vencimiento.isnot(None),
        ObligacionCliente.estado != 'cumplido',
    ).all():
        fv = oblig.fecha_vencimiento
        if fv is None:
            continue
        d = fv.date() if isinstance(fv, datetime) else fv
        if not (hoy <= d <= en_30):
            continue
        db.session.add(
            AlertaCompliance(
                cliente_id=oblig.cliente_id,
                tipo='vencimiento_obligacion',
                prioridad='alta',
                titulo='Vencimiento de obligación legal',
                descripcion=f'Revisar obligación (ID {oblig.id}) antes del {d.strftime("%d/%m/%Y")}.',
                fecha_vencimiento=oblig.fecha_vencimiento,
            )
        )
        creadas += 1
    if creadas:
        db.session.commit()
    return creadas
