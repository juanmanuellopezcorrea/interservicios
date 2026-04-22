from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from models import db, Usuario, Cliente, Trabajador, Tarea, RegistroHora, ControlLimites, FichajeControlHorario, TimerTrabajo, PlantillaTarea
from compliance_views import compliance_bp
from functools import wraps
from datetime import datetime, date, timedelta
from decimal import Decimal
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import io
import os
import secrets
import string
import uuid
from sqlalchemy import func, and_


def generar_contraseña(longitud=10):
    """Genera una contraseña aleatoria segura (letras + dígitos)."""
    alfabeto = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alfabeto) for _ in range(longitud))

app = Flask(__name__)
# Ruta absoluta a la base de datos (evita "readonly database" según desde dónde se ejecute la app)
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuración desde variables de entorno para producción (Vercel/Supabase)
# Prioridad: POSTGRES_URL (Supabase) > DATABASE_URL > SQLite local
DATABASE_URL = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Supabase/Vercel usan postgres:// pero SQLAlchemy requiere postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Desarrollo local: usar SQLite
    db_path = os.path.join(basedir, 'servicios_profesionales.db').replace('\\', '/')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-cambiar-en-produccion')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_ADMIN_REPORT_TO'] = os.environ.get('MAIL_ADMIN_REPORT_TO', 'acampos@interservicios.es')

db.init_app(app)

app.register_blueprint(compliance_bp)

from compliance_engine import seed_catalogo, CatalogoObligacion, ObligacionCliente, SolicitudPresupuesto
from models import CuestionarioNormativoCliente
from cuestionario_normativo_data import CUESTIONARIO, ids as cuestionario_ids
try:
    # Dependencia opcional (rapidfuzz). Si no está instalada, la app debe seguir arrancando.
    from conciliador_inteligente.main import ejecutar as conciliador_ejecutar
except Exception:
    conciliador_ejecutar = None


def _ensure_cuestionarios_normativos():
    """Crea el registro de cuestionario para clientes existentes si falta."""
    for c in Cliente.query.order_by(Cliente.id).all():
        if not CuestionarioNormativoCliente.query.filter_by(cliente_id=c.id).first():
            rec = CuestionarioNormativoCliente(cliente_id=c.id, respuestas_json='{}')
            data = {iid: 'PTE' for iid in cuestionario_ids()}
            rec.set_respuestas(data)
            db.session.add(rec)
    db.session.commit()


def _pendientes_por_cliente():
    """Devuelve lista de (cliente, pendientes[]) donde pendientes es lista de dicts del cuestionario."""
    out = []
    for c in Cliente.query.order_by(Cliente.nombre).all():
        rec = CuestionarioNormativoCliente.query.filter_by(cliente_id=c.id).first()
        if not rec:
            continue
        resp = rec.get_respuestas()
        pend = [row for row in CUESTIONARIO if resp.get(row['id'], 'PTE') in ('PTE', '')]
        if pend:
            out.append((c, pend))
    return out


def _enviar_informe_pendientes_admin():
    """Genera y envía al administrador un informe mensual de pendientes (si hay email configurado)."""
    pendientes = _pendientes_por_cliente()
    if not pendientes:
        return
    try:
        from flask_mail import Mail, Message
        mail = Mail(app)
        dest = app.config.get('MAIL_ADMIN_REPORT_TO') or app.config.get('MAIL_DESPACHO_ADDR') or app.config.get('MAIL_USERNAME', '')
        if not dest:
            return
        msg = Message('[Informe mensual] Pendientes cuestionario normativo', recipients=[dest])
        # HTML simple
        html = ["<h3>Pendientes cuestionario normativo</h3>"]
        for c, pend in pendientes:
            html.append(f"<h4>{c.nombre}</h4><ul>")
            for row in pend:
                html.append(f"<li><b>{row['campo']}</b></li>")
            html.append("</ul>")
        msg.html = "\n".join(html)
        mail.send(msg)
    except Exception:
        # Si no hay correo configurado, no rompemos la app
        return
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


@app.context_processor
def inject_fecha_actual():
    """Inyecta en todos los templates la fecha actual para enlaces del menú (mes/año)."""
    return {'now': date.today()}


# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para requerir rol de administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('rol') != 'ADMIN':
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para bloquear acceso de Trabajador (solo horas; sin Clientes/Tareas)
def no_trabajador_limitado(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('rol') == 'TRABAJADOR':
            flash('No tienes permiso para acceder a esta sección. Tu acceso está limitado a horas por cliente.', 'error')
            return redirect(url_for('horas_semana'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para informe de facturación (Admin o Trabajador facturación)
def facturacion_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('rol') not in ('ADMIN', 'TRABAJADOR_FACTURACION'):
            flash('Acceso denegado. Solo administradores y trabajadores de facturación pueden ver este informe.', 'error')
            return redirect(url_for('horas_semana'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_trabajador():
    """Obtener el trabajador actual (si la sesión es por Trabajador o por Usuario con trabajador_id)."""
    if session.get('trabajador_id'):
        return Trabajador.query.get(session['trabajador_id'])
    return None

# Función auxiliar para determinar clasificación de facturación
def calcular_clasificacion_facturacion(tarea, cliente, horas_trabajadas, trabajador):
    """
    Determina la clasificación de facturación según el nuevo sistema de cuotas.
    Cuando la tarea está fuera de cuota (no incluida en cuota o siempre facturable),
    el importe es SIEMPRE: horas × coste_hora del trabajador.
    Retorna: (clasificacion, importe_facturable, importe_manual)
    """
    # Si la tarea siempre es facturable → fuera de cuota, importe = horas × coste_hora
    if tarea.siempre_facturable:
        if tarea.tarifa_manual:
            return ('TARIFA_MANUAL', horas_trabajadas * trabajador.coste_hora, None)
        return ('FACTURABLE', horas_trabajadas * trabajador.coste_hora, None)
    
    # Verificar si está incluida en la cuota del cliente.
    # Prioridad: si el cliente tiene tareas_incluidas configuradas, esa lista es la fuente de verdad
    # (solo las tareas marcadas están incluidas; el resto son facturables).
    # Si el cliente no tiene tareas_incluidas, se usa la modalidad + flags de la tarea.
    incluida_en_cuota = False
    tareas_cliente = list(cliente.tareas_incluidas) if cliente.tareas_incluidas else []
    if tareas_cliente:
        # Lista explícita del cliente: solo está incluida si está en la lista
        incluida_en_cuota = tarea in tareas_cliente
    else:
        # Sin lista explícita: usar modalidad + flags de la tarea
        if cliente.modalidad_cuota == 'BASICO' and tarea.incluida_cuota_basica:
            incluida_en_cuota = True
        elif cliente.modalidad_cuota == 'PLUS' and tarea.incluida_cuota_estandar:
            incluida_en_cuota = True
        elif cliente.modalidad_cuota == 'PREMIUM' and tarea.incluida_cuota_premium:
            incluida_en_cuota = True
    
    # Si está incluida en cuota, no es facturable
    if incluida_en_cuota:
        return ('INCLUIDA_EN_CUOTA', Decimal(0), None)
    
    # Fuera de cuota (no incluida): importe = horas × coste_hora del trabajador
    if tarea.tarifa_manual:
        return ('TARIFA_MANUAL', horas_trabajadas * trabajador.coste_hora, None)
    return ('FACTURABLE', horas_trabajadas * trabajador.coste_hora, None)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        email = (email or '').strip()
        if email:
            trabajador = Trabajador.query.filter_by(email=email, activo=True).first()
            if trabajador and trabajador.check_password(password):
                session['user_id'] = trabajador.id
                session['username'] = trabajador.nombre
                session['rol'] = trabajador.rol
                session['trabajador_id'] = trabajador.id
                session['login_via'] = 'trabajador'
                flash('Sesión iniciada correctamente', 'success')
                if trabajador.es_admin():
                    return redirect(url_for('dashboard'))
                return redirect(url_for('horas_semana'))
            flash('Email o contraseña incorrectos', 'error')
            return redirect(url_for('login'))
        
        username = (username or '').strip()
        if not username:
            flash('Indica tu email o tu usuario', 'error')
            return redirect(url_for('login'))
        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and usuario.check_password(password):
            session['user_id'] = usuario.id
            session['username'] = usuario.username
            session['rol'] = usuario.rol
            session['trabajador_id'] = usuario.trabajador_id if usuario.trabajador_id else None
            session['login_via'] = 'usuario'
            flash('Sesión iniciada correctamente', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('login'))


@app.route('/cambiar-contrasena', methods=['GET', 'POST'])
@login_required
def cambiar_contrasena():
    """Permite al usuario cambiar su contraseña. Funciona para Trabajador (email) y Usuario (username)."""
    if request.method == 'POST':
        actual = request.form.get('password_actual', '')
        nueva = request.form.get('password_nueva', '')
        confirmar = request.form.get('password_confirmar', '')
        
        if not actual or not nueva or not confirmar:
            flash('Completa todos los campos', 'error')
            return render_template('cambiar_contrasena.html')
        if len(nueva) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('cambiar_contrasena.html')
        if nueva != confirmar:
            flash('La nueva contraseña y la confirmación no coinciden', 'error')
            return render_template('cambiar_contrasena.html')
        
        # Determinar si es Trabajador (login por email) o Usuario (login por username)
        es_trabajador = session.get('login_via') == 'trabajador' or (
            session.get('trabajador_id') == session.get('user_id') and
            Trabajador.query.get(session['user_id'])
        )
        if es_trabajador:
            trabajador = Trabajador.query.get(session['user_id'])
            if not trabajador or not trabajador.check_password(actual):
                flash('La contraseña actual no es correcta', 'error')
                return render_template('cambiar_contrasena.html')
            trabajador.set_password(nueva)
            db.session.commit()
        else:
            usuario = Usuario.query.get(session['user_id'])
            if not usuario or not usuario.check_password(actual):
                flash('La contraseña actual no es correcta', 'error')
                return render_template('cambiar_contrasena.html')
            usuario.set_password(nueva)
            db.session.commit()
        
        flash('Contraseña cambiada correctamente', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('cambiar_contrasena.html')


@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('rol') != 'ADMIN':
        return redirect(url_for('horas_semana'))
    return render_template('dashboard.html')


# ==================== CONCILIADOR INTELIGENTE ====================
@app.route('/conciliador', methods=['GET', 'POST'])
@login_required
def conciliador():
    if request.method == 'GET':
        return render_template('conciliador.html')

    if conciliador_ejecutar is None:
        flash('El conciliador no está disponible: falta instalar dependencias (rapidfuzz).', 'error')
        return redirect(url_for('conciliador'))

    facturas = request.files.get('facturas')
    banco = request.files.get('banco')

    if not facturas or not facturas.filename:
        flash('Selecciona el PDF de Facturas', 'error')
        return redirect(url_for('conciliador'))
    if not banco or not banco.filename:
        flash('Selecciona el PDF de Banco', 'error')
        return redirect(url_for('conciliador'))
    ext_ok = ('.pdf', '.xlsx', '.xls')
    if not any(facturas.filename.lower().endswith(e) for e in ext_ok) or not any(banco.filename.lower().endswith(e) for e in ext_ok):
        flash('Los archivos deben ser PDF o Excel (.pdf, .xlsx, .xls)', 'error')
        return redirect(url_for('conciliador'))

    run_id = uuid.uuid4().hex
    runs_dir = os.path.join(basedir, 'conciliador_runs')
    run_dir = os.path.join(runs_dir, run_id)
    input_dir = os.path.join(run_dir, 'input')
    output_dir = os.path.join(run_dir, 'output')
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    fact_ext = os.path.splitext(facturas.filename)[1].lower() or '.pdf'
    banco_ext = os.path.splitext(banco.filename)[1].lower() or '.pdf'
    fact_path = os.path.join(input_dir, 'facturas' + fact_ext)
    banco_path = os.path.join(input_dir, 'banco' + banco_ext)
    facturas.save(fact_path)
    banco.save(banco_path)

    try:
        r1, r2, fact_xlsx, banco_xlsx = conciliador_ejecutar(fact_path, banco_path, output_dir=output_dir)
    except Exception as e:
        flash(f'Error al conciliar: {e}', 'error')
        return redirect(url_for('conciliador'))

    session['conciliador_last_run_id'] = run_id
    return render_template(
        'conciliador_resultado.html',
        run_id=run_id,
        r1=r1,
        r2=r2,
        fact_xlsx=os.path.basename(fact_xlsx),
        banco_xlsx=os.path.basename(banco_xlsx),
    )


@app.route('/conciliador/<run_id>/descargar/<tipo>')
@login_required
def conciliador_descargar(run_id, tipo):
    runs_dir = os.path.join(basedir, 'conciliador_runs')
    run_dir = os.path.join(runs_dir, run_id, 'output')
    if tipo == 'facturas':
        path = os.path.join(run_dir, 'facturas_resultado.xlsx')
        download_name = 'facturas_resultado.xlsx'
    elif tipo == 'banco':
        path = os.path.join(run_dir, 'banco_resultado.xlsx')
        download_name = 'banco_resultado.xlsx'
    else:
        flash('Tipo de descarga no válido', 'error')
        return redirect(url_for('conciliador'))

    if not os.path.exists(path):
        flash('No se encontró el archivo exportado', 'error')
        return redirect(url_for('conciliador'))
    return send_file(path, as_attachment=True, download_name=download_name)

# ==================== CLIENTES ====================
@app.route('/clientes/importar', methods=['GET', 'POST'])
@login_required
def clientes_importar():
    if request.method == 'GET':
        return render_template('clientes_importar.html')

    file = request.files.get('archivo')
    if not file or file.filename == '':
        flash('Selecciona un archivo .xlsx', 'error')
        return redirect(url_for('clientes_importar'))
    if not file.filename.lower().endswith('.xlsx'):
        flash('El archivo debe ser Excel (.xlsx)', 'error')
        return redirect(url_for('clientes_importar'))

    try:
        data = file.read()
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as e:
        flash(f'No se pudo leer el Excel: {e}', 'error')
        return redirect(url_for('clientes_importar'))

    ws = wb.active
    rows = list(ws.iter_rows(min_row=1, values_only=True))
    wb.close()

    if len(rows) < 2:
        flash('El Excel no tiene datos (solo cabecera o vacío)', 'error')
        return redirect(url_for('clientes_importar'))

    headers = [str(c).strip() if c is not None else '' for c in rows[0]]
    col_nombre = col_tareas = None
    for i, h in enumerate(headers):
        h_lower = h.lower()
        if h_lower in ('cliente', 'nombre', 'nombre cliente'):
            col_nombre = i
        elif h_lower in ('tareas', 'tareas incluidas', 'tareas incluidas en contrato'):
            col_tareas = i
    if col_nombre is None:
        flash('No se encontró la columna de nombre del cliente (cliente / nombre).', 'error')
        return redirect(url_for('clientes_importar'))

    # Mapa nombre tarea -> Tarea para asignar tareas incluidas
    todas_tareas = {t.nombre.strip().lower(): t for t in Tarea.query.all()}

    creados = 0
    omitidos = 0
    for row in rows[1:]:
        nombre = row[col_nombre]
        if nombre is None or not str(nombre).strip():
            continue
        nombre = str(nombre).strip()
        if Cliente.query.filter_by(nombre=nombre).first():
            omitidos += 1
            continue
        cliente = Cliente(nombre=nombre, cuota_mensual=Decimal(0), precio_cuota_mensual=Decimal(0))
        db.session.add(cliente)
        db.session.flush()
        tareas_cliente = []
        if col_tareas is not None and row[col_tareas] is not None:
            texto = str(row[col_tareas]).strip()
            if texto:
                for nom in texto.split(';'):
                    nom = nom.strip()
                    if nom:
                        t = todas_tareas.get(nom.lower())
                        if t:
                            tareas_cliente.append(t)
        cliente.tareas_incluidas = tareas_cliente
        creados += 1

    db.session.commit()
    msg = f'Importación completada: {creados} clientes creados.'
    if omitidos:
        msg += f' {omitidos} omitidos (ya existían).'
    flash(msg, 'success')
    return redirect(url_for('clientes'))

@app.route('/clientes')
@login_required
def clientes():
    clientes_list = Cliente.query.order_by(Cliente.nombre).all()
    # Contar registros de horas para cada cliente
    clientes_con_contador = []
    for cliente in clientes_list:
        cliente.num_registros_horas = RegistroHora.query.filter_by(cliente_id=cliente.id).count()
        clientes_con_contador.append(cliente)
    return render_template('clientes.html', clientes=clientes_con_contador)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def cliente_nuevo():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        modalidad_cuota = request.form.get('modalidad_cuota', 'SIN_CUOTA')
        epigrafes_iae = request.form.get('epigrafes_iae_contratados', '0')
        horas_asesoria = request.form.get('horas_asesoria_fiscal_mes', '0')
        
        cliente = Cliente(
            nombre=nombre,
            cuota_mensual=Decimal(0),
            modalidad_cuota=modalidad_cuota,
            precio_cuota_mensual=Decimal(0),
            epigrafes_iae_contratados=int(epigrafes_iae) if epigrafes_iae.isdigit() else 0,
            horas_asesoria_fiscal_mes=Decimal(horas_asesoria) if horas_asesoria else Decimal('0')
        )
        db.session.add(cliente)
        db.session.flush()
        ids = [int(x) for x in request.form.getlist('tareas_incluidas') if x]
        cliente.tareas_incluidas = Tarea.query.filter(Tarea.id.in_(ids)).all() if ids else []
        # Crear cuestionario normativo para el nuevo cliente
        try:
            from models import CuestionarioNormativoCliente
            from cuestionario_normativo_data import ids as cuestionario_ids
            rec = CuestionarioNormativoCliente(cliente_id=cliente.id, respuestas_json='{}')
            data = {}
            for iid in cuestionario_ids():
                data[iid] = 'PTE'
            rec.set_respuestas(data)
            db.session.add(rec)
        except Exception:
            pass
        db.session.commit()
        flash('Cliente creado correctamente', 'success')
        return redirect(url_for('clientes'))
    
    tareas = Tarea.query.order_by(Tarea.nombre).all()
    return render_template('cliente_form.html', cliente=None, tareas=tareas)

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def cliente_editar(id):
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        cliente.nombre = request.form.get('nombre')
        cliente.cuota_mensual = Decimal(0)
        cliente.modalidad_cuota = request.form.get('modalidad_cuota', 'SIN_CUOTA')
        cliente.precio_cuota_mensual = Decimal(0)
        epigrafes_iae = request.form.get('epigrafes_iae_contratados', '0')
        cliente.epigrafes_iae_contratados = int(epigrafes_iae) if epigrafes_iae.isdigit() else 0
        horas_asesoria = request.form.get('horas_asesoria_fiscal_mes', '0')
        cliente.horas_asesoria_fiscal_mes = Decimal(horas_asesoria) if horas_asesoria else Decimal('0')
        ids = [int(x) for x in request.form.getlist('tareas_incluidas') if x]
        cliente.tareas_incluidas = Tarea.query.filter(Tarea.id.in_(ids)).all() if ids else []
        db.session.commit()
        flash('Cliente actualizado correctamente', 'success')
        return redirect(url_for('clientes'))
    
    tareas = Tarea.query.order_by(Tarea.nombre).all()
    return render_template('cliente_form.html', cliente=cliente, tareas=tareas)

@app.route('/clientes/eliminar/<int:id>', methods=['POST'])
@admin_required
def cliente_eliminar(id):
    cliente = Cliente.query.get_or_404(id)
    
    # Contar registros asociados
    registros_horas = RegistroHora.query.filter_by(cliente_id=id).count()
    controles_limites = ControlLimites.query.filter_by(cliente_id=id).count()
    
    # Eliminar registros de horas asociados
    if registros_horas > 0:
        RegistroHora.query.filter_by(cliente_id=id).delete()
    
    # Eliminar controles de límites asociados
    if controles_limites > 0:
        ControlLimites.query.filter_by(cliente_id=id).delete()
    
    # Eliminar relaciones con tareas (tabla intermedia)
    cliente.tareas_incluidas = []
    
    # Eliminar el cliente
    db.session.delete(cliente)
    db.session.commit()
    
    # Mensaje informativo
    mensaje = f'Cliente "{cliente.nombre}" eliminado correctamente'
    if registros_horas > 0:
        mensaje += f'. También se eliminaron {registros_horas} registro(s) de horas asociado(s)'
    if controles_limites > 0:
        mensaje += f'. También se eliminaron {controles_limites} control(es) de límites asociado(s)'
    
    flash(mensaje, 'success')
    return redirect(url_for('clientes'))

# ==================== TRABAJADORES ====================

@app.route('/trabajadores')
@admin_required
def trabajadores():
    trabajadores_list = Trabajador.query.order_by(Trabajador.nombre).all()
    # Contar registros de horas para cada trabajador
    trabajadores_con_contador = []
    for trabajador in trabajadores_list:
        trabajador.num_registros_horas = RegistroHora.query.filter_by(trabajador_id=trabajador.id).count()
        trabajadores_con_contador.append(trabajador)
    return render_template('trabajadores.html', trabajadores=trabajadores_con_contador)

@app.route('/trabajadores/nuevo', methods=['GET', 'POST'])
@admin_required
def trabajador_nuevo():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        rol = request.form.get('rol', 'TRABAJADOR')
        rol = rol if rol in ('ADMIN', 'TRABAJADOR', 'TRABAJADOR_FACTURACION') else 'TRABAJADOR'
        coste_hora = Decimal(request.form.get('coste_hora', 0))
        username = request.form.get('username', '').strip()

        if not nombre:
            flash('El nombre es obligatorio', 'error')
            return render_template('trabajador_form.html', trabajador=None)
        if email:
            if Trabajador.query.filter_by(email=email).first():
                flash('Ya existe un trabajador con ese email', 'error')
                return render_template('trabajador_form.html', trabajador=None)
            # La contraseña la determina el programa; el trabajador puede cambiarla después
            password = generar_contraseña()

        trabajador = Trabajador(
            nombre=nombre,
            email=email or None,
            rol=rol,
            coste_hora=coste_hora,
            activo=True,
        )
        if email and password:
            trabajador.set_password(password)
        db.session.add(trabajador)
        db.session.flush()

        if username and password and not email:
            if Usuario.query.filter_by(username=username).first():
                db.session.rollback()
                flash(f'El nombre de usuario "{username}" ya está en uso.', 'error')
                return render_template('trabajador_form.html', trabajador=None)
            usuario = Usuario(nombre=nombre, username=username, rol=rol, trabajador_id=trabajador.id)
            usuario.set_password(password)
            db.session.add(usuario)

        db.session.commit()
        flash('Trabajador creado correctamente', 'success')
        if email:
            flash(f'Usuario para login: {email}', 'info')
            flash(f'Contraseña asignada (comunicar al trabajador): {password}', 'info')
        return redirect(url_for('trabajadores'))

    return render_template('trabajador_form.html', trabajador=None)

@app.route('/trabajadores/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def trabajador_editar(id):
    trabajador = Trabajador.query.get_or_404(id)

    if request.method == 'POST':
        trabajador.nombre = request.form.get('nombre', '').strip()
        trabajador.coste_hora = Decimal(request.form.get('coste_hora', 0))
        trabajador.activo = request.form.get('activo') == '1'
        rol = request.form.get('rol', 'TRABAJADOR')
        trabajador.rol = rol if rol in ('ADMIN', 'TRABAJADOR', 'TRABAJADOR_FACTURACION') else trabajador.rol
        email = request.form.get('email', '').strip()
        if email:
            otro = Trabajador.query.filter_by(email=email).first()
            if otro and otro.id != trabajador.id:
                flash('Ese email ya está asignado a otro trabajador', 'error')
                return render_template('trabajador_form.html', trabajador=trabajador)
            trabajador.email = email
        else:
            trabajador.email = None
        nueva_password = request.form.get('password', '')
        if nueva_password and len(nueva_password) >= 6:
            trabajador.set_password(nueva_password)
        db.session.commit()
        flash('Trabajador actualizado correctamente', 'success')
        return redirect(url_for('trabajadores'))

    return render_template('trabajador_form.html', trabajador=trabajador)

@app.route('/trabajadores/eliminar/<int:id>', methods=['POST'])
@admin_required
def trabajador_eliminar(id):
    trabajador = Trabajador.query.get_or_404(id)
    
    # Contar registros asociados
    registros_horas = RegistroHora.query.filter_by(trabajador_id=id).count()
    
    # Verificar si tiene usuario asociado
    usuario_asociado = Usuario.query.filter_by(trabajador_id=id).first()
    
    # Eliminar registros de horas asociados
    if registros_horas > 0:
        RegistroHora.query.filter_by(trabajador_id=id).delete()
    
    # Eliminar usuario asociado si existe
    if usuario_asociado:
        db.session.delete(usuario_asociado)
    
    # Eliminar el trabajador
    db.session.delete(trabajador)
    db.session.commit()
    
    # Mensaje informativo
    mensaje = f'Trabajador "{trabajador.nombre}" eliminado correctamente'
    if registros_horas > 0:
        mensaje += f'. También se eliminaron {registros_horas} registro(s) de horas asociado(s)'
    if usuario_asociado:
        mensaje += f'. También se eliminó el usuario asociado "{usuario_asociado.username}"'
    
    flash(mensaje, 'success')
    return redirect(url_for('trabajadores'))

# ==================== TAREAS ====================

@app.route('/tareas')
@login_required
def tareas():
    tareas_list = Tarea.query.order_by(Tarea.nombre).all()
    # Contar registros de horas para cada tarea
    tareas_con_contador = []
    for tarea in tareas_list:
        tarea.num_registros_horas = RegistroHora.query.filter_by(tarea_id=tarea.id).count()
        tareas_con_contador.append(tarea)
    return render_template('tareas.html', tareas=tareas_con_contador)

@app.route('/tareas/nuevo', methods=['GET', 'POST'])
@login_required
def tarea_nuevo():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        tipo_tarea = request.form.get('tipo_tarea', 'CLIENTE')
        incluida_cuota_basica = request.form.get('incluida_cuota_basica') == '1'
        incluida_cuota_estandar = request.form.get('incluida_cuota_estandar') == '1'
        incluida_cuota_premium = request.form.get('incluida_cuota_premium') == '1'
        siempre_facturable = request.form.get('siempre_facturable') == '1'
        tipo_limite = request.form.get('tipo_limite', 'NINGUNO')
        valor_limite = request.form.get('valor_limite')
        tarifa_hora_fuera_cuota = request.form.get('tarifa_hora_fuera_cuota') == '1'
        precio_fijo_fuera_cuota = request.form.get('precio_fijo_fuera_cuota')
        tarifa_manual = request.form.get('tarifa_manual') == '1'
        categoria = request.form.get('categoria', '').strip()
        requiere_cliente = request.form.get('requiere_cliente') != '0'
        notas = request.form.get('notas', '').strip()
        
        # Compatibilidad: mantener incluida_contrato si alguna cuota está incluida
        incluida_contrato = incluida_cuota_basica or incluida_cuota_estandar or incluida_cuota_premium
        
        tarea = Tarea(
            nombre=nombre,
            tipo_tarea=tipo_tarea,
            incluida_cuota_basica=incluida_cuota_basica,
            incluida_cuota_estandar=incluida_cuota_estandar,
            incluida_cuota_premium=incluida_cuota_premium,
            siempre_facturable=siempre_facturable,
            tipo_limite=tipo_limite,
            valor_limite=int(valor_limite) if valor_limite and valor_limite.isdigit() else None,
            tarifa_hora_fuera_cuota=tarifa_hora_fuera_cuota,
            precio_fijo_fuera_cuota=Decimal(precio_fijo_fuera_cuota) if precio_fijo_fuera_cuota else None,
            tarifa_manual=tarifa_manual,
            categoria=categoria if categoria else None,
            requiere_cliente=requiere_cliente,
            notas=notas if notas else None,
            # Campos antiguos para compatibilidad
            incluida_contrato=incluida_contrato,
            precio_hora=Decimal(precio_fijo_fuera_cuota) if precio_fijo_fuera_cuota and tarifa_hora_fuera_cuota else None
        )
        db.session.add(tarea)
        db.session.commit()
        flash('Tarea creada correctamente', 'success')
        return redirect(url_for('tareas'))
    
    return render_template('tarea_form.html', tarea=None)

@app.route('/tareas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def tarea_editar(id):
    tarea = Tarea.query.get_or_404(id)
    
    if request.method == 'POST':
        tarea.nombre = request.form.get('nombre')
        tarea.tipo_tarea = request.form.get('tipo_tarea', 'CLIENTE')
        tarea.incluida_cuota_basica = request.form.get('incluida_cuota_basica') == '1'
        tarea.incluida_cuota_estandar = request.form.get('incluida_cuota_estandar') == '1'
        tarea.incluida_cuota_premium = request.form.get('incluida_cuota_premium') == '1'
        tarea.siempre_facturable = request.form.get('siempre_facturable') == '1'
        tarea.tipo_limite = request.form.get('tipo_limite', 'NINGUNO')
        valor_limite = request.form.get('valor_limite')
        tarea.valor_limite = int(valor_limite) if valor_limite and valor_limite.isdigit() else None
        tarea.tarifa_hora_fuera_cuota = request.form.get('tarifa_hora_fuera_cuota') == '1'
        precio_fijo_fuera_cuota = request.form.get('precio_fijo_fuera_cuota')
        tarea.precio_fijo_fuera_cuota = Decimal(precio_fijo_fuera_cuota) if precio_fijo_fuera_cuota else None
        tarea.tarifa_manual = request.form.get('tarifa_manual') == '1'
        categoria = request.form.get('categoria', '').strip()
        tarea.categoria = categoria if categoria else None
        tarea.requiere_cliente = request.form.get('requiere_cliente') != '0'
        notas = request.form.get('notas', '').strip()
        tarea.notas = notas if notas else None
        
        # Compatibilidad: mantener incluida_contrato si alguna cuota está incluida
        tarea.incluida_contrato = tarea.incluida_cuota_basica or tarea.incluida_cuota_estandar or tarea.incluida_cuota_premium
        tarea.precio_hora = tarea.precio_fijo_fuera_cuota if tarea.tarifa_hora_fuera_cuota else None
        
        db.session.commit()
        flash('Tarea actualizada correctamente', 'success')
        return redirect(url_for('tareas'))
    
    return render_template('tarea_form.html', tarea=tarea)

@app.route('/tareas/eliminar/<int:id>', methods=['POST'])
@login_required
def tarea_eliminar(id):
    tarea = Tarea.query.get_or_404(id)
    
    # Contar registros asociados
    registros_horas = RegistroHora.query.filter_by(tarea_id=id).count()
    controles_limites = ControlLimites.query.filter_by(tarea_id=id).count()
    
    # Eliminar registros de horas asociados
    if registros_horas > 0:
        RegistroHora.query.filter_by(tarea_id=id).delete()
    
    # Eliminar controles de límites asociados
    if controles_limites > 0:
        ControlLimites.query.filter_by(tarea_id=id).delete()
    
    # Eliminar relaciones con clientes (tabla intermedia)
    tarea.clientes = []
    
    # Eliminar la tarea
    db.session.delete(tarea)
    db.session.commit()
    
    # Mensaje informativo
    mensaje = f'Tarea "{tarea.nombre}" eliminada correctamente'
    if registros_horas > 0:
        mensaje += f'. También se eliminaron {registros_horas} registro(s) de horas asociado(s)'
    if controles_limites > 0:
        mensaje += f'. También se eliminaron {controles_limites} control(es) de límites asociado(s)'
    
    flash(mensaje, 'success')
    return redirect(url_for('tareas'))

@app.route('/tareas/importar', methods=['GET', 'POST'])
@login_required
def tareas_importar():
    if request.method == 'GET':
        return render_template('tareas_importar.html')

    file = request.files.get('archivo')
    if not file or file.filename == '':
        flash('Selecciona un archivo .xlsx', 'error')
        return redirect(url_for('tareas_importar'))
    if not file.filename.lower().endswith('.xlsx'):
        flash('El archivo debe ser Excel (.xlsx)', 'error')
        return redirect(url_for('tareas_importar'))

    try:
        data = file.read()
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as e:
        flash(f'No se pudo leer el Excel: {e}', 'error')
        return redirect(url_for('tareas_importar'))

    sheet_name = 'Tabla Maestra Tareas'
    if sheet_name not in wb.sheetnames:
        sheet_name = wb.sheetnames[0]
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(min_row=1, values_only=True))
    wb.close()

    if len(rows) < 2:
        flash('El Excel no tiene datos (solo cabecera o vacío)', 'error')
        return redirect(url_for('tareas_importar'))

    headers = [str(c).strip() if c is not None else '' for c in rows[0]]
    col_nombre = col_incluida = col_facturacion = None
    for i, h in enumerate(headers):
        h_lower = h.lower()
        if 'nombre' in h_lower and 'tarea' in h_lower:
            col_nombre = i
        elif 'incluida' in h_lower and 'cuota' in h_lower:
            col_incluida = i
        elif 'facturaci' in h_lower or 'facturacion' in h_lower:
            col_facturacion = i
    if col_nombre is None:
        flash('No se encontró la columna "Nombre de la tarea" en el Excel.', 'error')
        return redirect(url_for('tareas_importar'))

    creadas = 0
    omitidas = 0
    for row in rows[1:]:
        nombre = row[col_nombre]
        if nombre is None or not str(nombre).strip():
            continue
        nombre = str(nombre).strip()
        if Tarea.query.filter_by(nombre=nombre).first():
            omitidas += 1
            continue
        incluida = True
        if col_incluida is not None and row[col_incluida] is not None:
            val = str(row[col_incluida]).strip().lower()
            incluida = val in ('sí', 'si', 's', '1', 'true', 'yes')
        precio_hora = None
        if not incluida and col_facturacion is not None and row[col_facturacion] is not None:
            try:
                v = row[col_facturacion]
                if isinstance(v, (int, float)):
                    precio_hora = Decimal(str(v))
                else:
                    precio_hora = Decimal(str(v).replace(',', '.'))
            except Exception:
                pass
        t = Tarea(nombre=nombre, incluida_contrato=incluida, precio_hora=precio_hora)
        db.session.add(t)
        creadas += 1

    db.session.commit()
    msg = f'Importación completada: {creadas} tareas creadas.'
    if omitidas:
        msg += f' {omitidas} omitidas (ya existían).'
    flash(msg, 'success')
    return redirect(url_for('tareas'))

# ==================== REGISTRO DE HORAS ====================

@app.route('/horas')
@login_required
def horas():
    if session.get('rol') == 'ADMIN':
        horas_list = RegistroHora.query.order_by(RegistroHora.fecha.desc()).all()
    else:
        trabajador_id = session.get('trabajador_id')
        if not trabajador_id:
            flash('No tienes un trabajador asociado', 'error')
            return redirect(url_for('dashboard'))
        horas_list = RegistroHora.query.filter_by(trabajador_id=trabajador_id).order_by(RegistroHora.fecha.desc()).all()
    
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    tareas = Tarea.query.order_by(Tarea.nombre).all()
    
    trabajadores = []
    if session.get('rol') == 'ADMIN':
        trabajadores = Trabajador.query.order_by(Trabajador.nombre).all()
    
    return render_template('horas.html', horas=horas_list, clientes=clientes, tareas=tareas, trabajadores=trabajadores)

# ==================== REGISTRO RÁPIDO (compatibilidad navbar) ====================
# En algunos despliegues/plantillas existe el enlace `url_for('horas_registro_rapido')`.
# Si la ruta no estaba definida, la app rompe al renderizar cualquier vista.
@app.route('/horas/registro-rapido', methods=['GET', 'POST'])
@login_required
def horas_registro_rapido():
    modo = (request.args.get('modo') or 'quick').strip()
    if modo not in ('quick', 'visual'):
        modo = 'quick'

    hoy = date.today()
    hoy_str = hoy.strftime('%Y-%m-%d')

    clientes = Cliente.query.order_by(Cliente.nombre).all()
    tareas = Tarea.query.order_by(Tarea.nombre).all()

    # Admin puede seleccionar trabajador; resto solo el suyo
    trabajador_id = session.get('trabajador_id')
    trabajadores = []
    if session.get('rol') == 'ADMIN':
        trabajadores = Trabajador.query.order_by(Trabajador.nombre).all()
        trabajador_id = request.args.get('trabajador_id', type=int) or trabajador_id

    # Prefill desde enlaces "repetir"
    pre_cliente_id = request.args.get('cliente_id', type=int)
    pre_tarea_id = request.args.get('tarea_id', type=int)

    # POST: guardar horas o gestionar plantillas
    if request.method == 'POST':
        accion = (request.form.get('accion') or '').strip()
        modo_post = (request.form.get('modo') or modo).strip()

        # Admin puede postear trabajador_id; resto forzar al suyo
        if session.get('rol') == 'ADMIN':
            trabajador_id_post = request.form.get('trabajador_id', type=int) or trabajador_id
        else:
            trabajador_id_post = trabajador_id

        if not trabajador_id_post:
            flash('No tienes un trabajador asociado', 'error')
            return redirect(url_for('horas_registro_rapido', modo=modo_post))

        if accion in ('editar_plantilla', 'eliminar_plantilla', 'crear_plantilla'):
            if accion == 'crear_plantilla':
                nombre_pl = (request.form.get('nombre_plantilla') or '').strip()
                cliente_id_pl = request.form.get('cliente_id', type=int)
                tarea_id_pl = request.form.get('tarea_id', type=int)
                horas_pl = (request.form.get('horas_plantilla') or '1').strip().replace(',', '.')
                desc_pl = (request.form.get('descripcion_plantilla') or '').strip()
                if not nombre_pl:
                    flash('Indica un nombre para la plantilla', 'error')
                    return redirect(url_for('horas_registro_rapido', modo=modo_post))
                if not cliente_id_pl:
                    flash('Selecciona un cliente válido antes de guardar la plantilla', 'error')
                    return redirect(url_for('horas_registro_rapido', modo=modo_post))
                if not tarea_id_pl:
                    flash('Selecciona una tarea válida antes de guardar la plantilla', 'error')
                    return redirect(url_for('horas_registro_rapido', modo=modo_post))
                try:
                    horas_dec = Decimal(horas_pl)
                except Exception:
                    horas_dec = Decimal('1')
                pl = PlantillaTarea(
                    trabajador_id=trabajador_id_post,
                    nombre=nombre_pl,
                    cliente_id=cliente_id_pl,
                    tarea_id=tarea_id_pl,
                    horas_default=horas_dec,
                    descripcion_default=desc_pl if desc_pl else None,
                    activa=True,
                )
                db.session.add(pl)
                db.session.commit()
                flash('Plantilla creada', 'success')
                return redirect(url_for('horas_registro_rapido', modo=modo_post))

            plantilla_id = request.form.get('plantilla_id', type=int)
            pl = PlantillaTarea.query.filter_by(id=plantilla_id, trabajador_id=trabajador_id_post).first()
            if not pl:
                flash('Plantilla no encontrada', 'error')
                return redirect(url_for('horas_registro_rapido', modo=modo_post))

            if accion == 'eliminar_plantilla':
                db.session.delete(pl)
                db.session.commit()
                flash('Plantilla eliminada', 'success')
                return redirect(url_for('horas_registro_rapido', modo=modo_post))

            # editar_plantilla
            pl.nombre = (request.form.get('edit_nombre') or pl.nombre).strip()
            pl.cliente_id = request.form.get('edit_cliente_id', type=int) or pl.cliente_id
            pl.tarea_id = request.form.get('edit_tarea_id', type=int) or pl.tarea_id
            horas_pl = (request.form.get('edit_horas') or str(pl.horas_default)).strip().replace(',', '.')
            try:
                pl.horas_default = Decimal(horas_pl)
            except Exception:
                pass
            desc_pl = (request.form.get('edit_descripcion') or '').strip()
            pl.descripcion_default = desc_pl if desc_pl else None
            db.session.commit()
            flash('Plantilla actualizada', 'success')
            return redirect(url_for('horas_registro_rapido', modo=modo_post))

        # Guardar horas (preset minutos o horas_custom)
        cliente_id = request.form.get('cliente_id', type=int)
        tarea_id = request.form.get('tarea_id', type=int)
        fecha_str = (request.form.get('fecha') or hoy_str).strip()
        observaciones = (request.form.get('observaciones') or '').strip()

        preset_min = request.form.get('preset_minutos')
        horas_custom = (request.form.get('horas_custom') or '').strip().replace(',', '.')
        minutos = None
        if preset_min and str(preset_min).isdigit():
            minutos = int(preset_min)
            horas_dec = Decimal(str(minutos)) / Decimal('60')
        else:
            try:
                horas_dec = Decimal(horas_custom)
            except Exception:
                horas_dec = Decimal('0')

        # mínimo 5 minutos
        if horas_dec < (Decimal('5') / Decimal('60')):
            flash('El mínimo por registro son 5 minutos', 'error')
            return redirect(url_for('horas_registro_rapido', modo=modo_post))

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except Exception:
            fecha = hoy

        trabajador = Trabajador.query.get(trabajador_id_post)
        tarea = Tarea.query.get(tarea_id) if tarea_id else None
        cliente = Cliente.query.get(cliente_id) if cliente_id else None
        if not trabajador or not tarea or not cliente:
            flash('Selecciona cliente y tarea válidos', 'error')
            return redirect(url_for('horas_registro_rapido', modo=modo_post))

        coste_total = horas_dec * trabajador.coste_hora
        clasificacion, importe_facturable, importe_manual = calcular_clasificacion_facturacion(tarea, cliente, horas_dec, trabajador)
        importe_facturar = importe_facturable if importe_facturable else Decimal(0)

        reg = RegistroHora(
            trabajador_id=trabajador_id_post,
            cliente_id=cliente_id,
            tarea_id=tarea_id,
            fecha=fecha,
            horas=horas_dec,
            coste_total=coste_total,
            importe_facturar=importe_facturar,
            clasificacion_facturacion=clasificacion,
            importe_facturable=importe_facturable,
            importe_manual=importe_manual,
            observaciones=observaciones if observaciones else None,
        )
        db.session.add(reg)
        db.session.commit()
        flash('Registro guardado', 'success')
        return redirect(url_for('horas_registro_rapido', modo=modo_post, cliente_id=cliente_id, tarea_id=tarea_id))

    plantillas = []
    ultimos = []
    top_clientes = []
    if trabajador_id:
        plantillas = (
            PlantillaTarea.query
            .filter_by(trabajador_id=trabajador_id, activa=True)
            .order_by(PlantillaTarea.nombre.asc())
            .all()
        )
        ultimos = (
            RegistroHora.query
            .filter_by(trabajador_id=trabajador_id)
            .order_by(RegistroHora.fecha.desc(), RegistroHora.id.desc())
            .limit(12)
            .all()
        )
        # Clientes más usados en los últimos 30 días (para modo visual)
        desde_30 = date.today() - timedelta(days=30)
        rows = (
            db.session.query(Cliente.id, Cliente.nombre, func.sum(RegistroHora.horas).label('h'))
            .join(RegistroHora, RegistroHora.cliente_id == Cliente.id)
            .filter(RegistroHora.trabajador_id == trabajador_id, RegistroHora.fecha >= desde_30)
            .group_by(Cliente.id, Cliente.nombre)
            .order_by(func.sum(RegistroHora.horas).desc())
            .limit(18)
            .all()
        )
        top_clientes = [{'id': rid, 'nombre': rnom, 'horas': float(rh or 0)} for (rid, rnom, rh) in rows]

    return render_template(
        'horas_registro_rapido.html',
        modo=modo,
        hoy_str=hoy_str,
        clientes=clientes,
        tareas=tareas,
        trabajadores=trabajadores,
        trabajador_id=trabajador_id,
        pre_cliente_id=pre_cliente_id,
        pre_tarea_id=pre_tarea_id,
        plantillas=plantillas,
        ultimos=ultimos,
        top_clientes=top_clientes,
    )


# ==================== CONTROL HORARIO ====================
@app.route('/control-horario', methods=['GET'])
@login_required
def control_horario():
    # Niveles:
    # 1 -> trabajador normal (solo sus datos)
    # 2 -> trabajador facturación (resumen semanal)
    # 3 -> admin (resumen completo + alertas + edición)
    rol = session.get('rol')
    if rol == 'ADMIN':
        nivel = 3
    elif rol == 'TRABAJADOR_FACTURACION':
        nivel = 2
    else:
        nivel = 1

    hoy = date.today()
    # Rango semanal por defecto (para filtros del informe Excel en la plantilla)
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)
    tid = session.get('trabajador_id')

    fichaje_activo = None
    fichajes_hoy = []
    horas_semana = 0.0
    horas_mes = 0.0
    horas_anio = 0.0
    limite_anual = 1800  # valor por defecto

    if tid:
        fichaje_activo = FichajeControlHorario.query.filter_by(trabajador_id=tid, fecha=hoy, hora_salida=None).first()
        fichajes_hoy = (
            FichajeControlHorario.query.filter_by(trabajador_id=tid, fecha=hoy)
            .order_by(FichajeControlHorario.hora_entrada.asc())
            .all()
        )

        # usa lunes/domingo calculados arriba
        regs_sem = FichajeControlHorario.query.filter(
            FichajeControlHorario.trabajador_id == tid,
            FichajeControlHorario.fecha >= lunes,
            FichajeControlHorario.fecha <= domingo,
            FichajeControlHorario.horas_trabajadas.isnot(None),
        ).all()
        horas_semana = float(sum(r.horas_trabajadas for r in regs_sem if r.horas_trabajadas is not None) or 0)

        inicio_mes = date(hoy.year, hoy.month, 1)
        fin_mes = date(hoy.year + (1 if hoy.month == 12 else 0), 1 if hoy.month == 12 else hoy.month + 1, 1)
        regs_mes = FichajeControlHorario.query.filter(
            FichajeControlHorario.trabajador_id == tid,
            FichajeControlHorario.fecha >= inicio_mes,
            FichajeControlHorario.fecha < fin_mes,
            FichajeControlHorario.horas_trabajadas.isnot(None),
        ).all()
        horas_mes = float(sum(r.horas_trabajadas for r in regs_mes if r.horas_trabajadas is not None) or 0)

        inicio_anio = date(hoy.year, 1, 1)
        fin_anio = date(hoy.year + 1, 1, 1)
        regs_anio = FichajeControlHorario.query.filter(
            FichajeControlHorario.trabajador_id == tid,
            FichajeControlHorario.fecha >= inicio_anio,
            FichajeControlHorario.fecha < fin_anio,
            FichajeControlHorario.horas_trabajadas.isnot(None),
        ).all()
        horas_anio = float(sum(r.horas_trabajadas for r in regs_anio if r.horas_trabajadas is not None) or 0)

    resumen_todos = []
    alertas = []
    fichajes_editar_estado = []

    trabajadores_lista = []
    if nivel >= 2:
        trabajadores_lista = Trabajador.query.filter_by(activo=True).order_by(Trabajador.nombre).all()
        inicio_mes = date(hoy.year, hoy.month, 1)
        fin_mes = date(hoy.year + (1 if hoy.month == 12 else 0), 1 if hoy.month == 12 else hoy.month + 1, 1)
        inicio_anio = date(hoy.year, 1, 1)
        fin_anio = date(hoy.year + 1, 1, 1)

        for t in trabajadores_lista:
            fichaje_act = FichajeControlHorario.query.filter_by(trabajador_id=t.id, fecha=hoy, hora_salida=None).first()
            hoy_regs = FichajeControlHorario.query.filter(
                FichajeControlHorario.trabajador_id == t.id,
                FichajeControlHorario.fecha == hoy,
                FichajeControlHorario.horas_trabajadas.isnot(None),
            ).all()
            semana_regs = FichajeControlHorario.query.filter(
                FichajeControlHorario.trabajador_id == t.id,
                FichajeControlHorario.fecha >= lunes,
                FichajeControlHorario.fecha <= domingo,
                FichajeControlHorario.horas_trabajadas.isnot(None),
            ).all()

            mes_total = None
            anio_total = None
            if nivel == 3:
                mes_regs = FichajeControlHorario.query.filter(
                    FichajeControlHorario.trabajador_id == t.id,
                    FichajeControlHorario.fecha >= inicio_mes,
                    FichajeControlHorario.fecha < fin_mes,
                    FichajeControlHorario.horas_trabajadas.isnot(None),
                ).all()
                anio_regs = FichajeControlHorario.query.filter(
                    FichajeControlHorario.trabajador_id == t.id,
                    FichajeControlHorario.fecha >= inicio_anio,
                    FichajeControlHorario.fecha < fin_anio,
                    FichajeControlHorario.horas_trabajadas.isnot(None),
                ).all()
                mes_total = float(sum(r.horas_trabajadas for r in mes_regs if r.horas_trabajadas is not None) or 0)
                anio_total = float(sum(r.horas_trabajadas for r in anio_regs if r.horas_trabajadas is not None) or 0)

                if limite_anual and anio_total is not None:
                    pct = (anio_total / float(limite_anual)) * 100
                    if pct >= 100:
                        alertas.append({'tipo': 'critica', 'nombre': t.nombre, 'horas': anio_total})
                    elif pct >= 90:
                        alertas.append({'tipo': 'preventiva', 'nombre': t.nombre, 'horas': anio_total})

            resumen_todos.append({
                'nombre': t.nombre,
                'estado_fichado': bool(fichaje_act),
                'hoy': float(sum(r.horas_trabajadas for r in hoy_regs if r.horas_trabajadas is not None) or 0),
                'semana': float(sum(r.horas_trabajadas for r in semana_regs if r.horas_trabajadas is not None) or 0),
                'mes': mes_total,
                'anio': anio_total,
            })

        if nivel == 3:
            desde = hoy - timedelta(days=31)
            fichajes_editar_estado = (
                FichajeControlHorario.query.filter(
                    FichajeControlHorario.fecha >= desde,
                    FichajeControlHorario.fecha <= hoy,
                    FichajeControlHorario.hora_salida.isnot(None),
                )
                .order_by(FichajeControlHorario.fecha.desc())
                .limit(200)
                .all()
            )

    return render_template(
        'control_horario.html',
        nivel=nivel,
        alertas=alertas,
        fichaje_activo=fichaje_activo,
        fichajes_hoy=fichajes_hoy,
        total_hoy=float(sum(f.horas_trabajadas for f in fichajes_hoy if f.horas_trabajadas is not None) or 0),
        horas_semana=horas_semana,
        horas_mes=horas_mes,
        horas_anio=horas_anio,
        resumen_todos=resumen_todos,
        fichajes_editar_estado=fichajes_editar_estado,
        limite_anual=limite_anual,
        lunes=lunes,
        domingo=domingo,
        trabajadores_lista=trabajadores_lista,
    )


@app.route('/control-horario/fichar', methods=['POST'])
@login_required
def control_horario_fichar():
    tid = session.get('trabajador_id')
    if not tid:
        flash('No tienes un trabajador asociado; el fichaje no está disponible.', 'error')
        return redirect(url_for('control_horario'))

    ahora = datetime.now()
    hoy = ahora.date()
    activo = FichajeControlHorario.query.filter_by(trabajador_id=tid, fecha=hoy, hora_salida=None).first()

    if activo:
        activo.hora_salida = ahora.time()
        dt_in = datetime.combine(hoy, activo.hora_entrada)
        dt_out = datetime.combine(hoy, activo.hora_salida)
        segundos = max(0, int((dt_out - dt_in).total_seconds()))
        activo.horas_trabajadas = round(Decimal(segundos) / Decimal(3600), 2)
        flash('Salida registrada.', 'success')
    else:
        nuevo = FichajeControlHorario(
            trabajador_id=tid,
            fecha=hoy,
            hora_entrada=ahora.time(),
            hora_salida=None,
            horas_trabajadas=None,
            ubicacion='Oficina',
            estado='Pendiente',
        )
        db.session.add(nuevo)
        flash('Entrada registrada.', 'success')

    db.session.commit()
    return redirect(url_for('control_horario'))


@app.route('/control-horario/cambiar-estado', methods=['POST'])
@admin_required
def control_horario_cambiar_estado():
    fichaje_id = request.form.get('fichaje_id', type=int)
    nuevo_estado = request.form.get('estado', '').strip()
    if not fichaje_id:
        flash('Falta fichaje_id.', 'error')
        return redirect(url_for('control_horario'))
    if nuevo_estado not in ('Pendiente', 'Aprobado'):
        flash('Estado inválido.', 'error')
        return redirect(url_for('control_horario'))
    f = FichajeControlHorario.query.get_or_404(fichaje_id)
    f.estado = nuevo_estado
    db.session.commit()
    flash('Estado actualizado.', 'success')
    return redirect(url_for('control_horario'))


@app.route('/control-horario/informe/excel', methods=['GET'])
@login_required
def control_horario_informe_excel():
    if session.get('rol') != 'ADMIN':
        tid = session.get('trabajador_id')
        if not tid:
            flash('No tienes un trabajador asociado.', 'error')
            return redirect(url_for('control_horario'))
        regs = (
            FichajeControlHorario.query.filter_by(trabajador_id=tid)
            .order_by(FichajeControlHorario.fecha.desc(), FichajeControlHorario.hora_entrada.desc())
            .limit(2000)
            .all()
        )
    else:
        regs = (
            FichajeControlHorario.query.order_by(FichajeControlHorario.fecha.desc(), FichajeControlHorario.id.desc())
            .limit(5000)
            .all()
        )

    wb = Workbook()
    ws = wb.active
    ws.title = "Control horario"
    ws.append(["Fecha", "Trabajador", "Entrada", "Salida", "Horas", "Estado", "Ubicación"])
    for r in regs:
        ws.append([
            r.fecha.strftime('%Y-%m-%d') if r.fecha else '',
            r.trabajador.nombre if r.trabajador else str(r.trabajador_id),
            r.hora_entrada.strftime('%H:%M:%S') if r.hora_entrada else '',
            r.hora_salida.strftime('%H:%M:%S') if r.hora_salida else '',
            float(r.horas_trabajadas) if r.horas_trabajadas is not None else '',
            r.estado or '',
            r.ubicacion or '',
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"control_horario_{date.today().strftime('%Y%m%d')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route('/api/control-horario/estado', methods=['GET'])
@login_required
def control_horario_estado():
    """Estado de fichaje para el widget del navbar."""
    tid = session.get('trabajador_id')
    if not tid:
        return jsonify({'fichado': False, 'error': 'No tienes un trabajador asociado'}), 200

    hoy = date.today()
    activo = FichajeControlHorario.query.filter_by(trabajador_id=tid, fecha=hoy, hora_salida=None).first()
    if not activo:
        return jsonify({'fichado': False}), 200

    ahora = datetime.now()
    dt_in = datetime.combine(hoy, activo.hora_entrada)
    segundos = max(0, int((ahora - dt_in).total_seconds()))
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    tiempo = f"{h:02d}:{m:02d}:{s:02d}"
    return jsonify({
        'fichado': True,
        'fecha': hoy.strftime('%Y-%m-%d'),
        'hora_entrada': activo.hora_entrada.strftime('%H:%M:%S') if activo.hora_entrada else None,
        'segundos': segundos,
        'tiempo': tiempo,
    }), 200


# ==================== API TIMER (Registro rápido / widget navbar) ====================
@app.route('/api/timer/estado', methods=['GET'])
@login_required
def api_timer_estado():
    tid = session.get('trabajador_id')
    if not tid:
        return jsonify({'activo': False, 'error': 'No tienes un trabajador asociado'}), 200

    t = TimerTrabajo.query.filter_by(trabajador_id=tid).first()
    if not t:
        return jsonify({'activo': False}), 200

    now_dt = datetime.now()
    base_seconds = int(t.accumulated_seconds or 0)
    if not t.is_paused and t.started_at:
        base_seconds += max(0, int((now_dt - t.started_at).total_seconds()))

    cliente = Cliente.query.get(t.cliente_id)
    tarea = Tarea.query.get(t.tarea_id)
    h = base_seconds // 3600
    m = (base_seconds % 3600) // 60
    s = base_seconds % 60
    texto = f"{h:02d}:{m:02d}:{s:02d}"
    return jsonify({
        'activo': True,
        'segundos': base_seconds,
        'cliente': cliente.nombre if cliente else '',
        'tarea': tarea.nombre if tarea else '',
        'texto': texto,
        'pausado': bool(t.is_paused),
    }), 200


# ==================== API REGISTRO RÁPIDO (para horas_registro_rapido.html) ====================

@app.route('/api/clientes/buscar', methods=['GET'])
@login_required
def api_clientes_buscar():
    q = (request.args.get('q') or '').strip().lower()
    if len(q) < 2:
        return jsonify([]), 200
    items = (
        Cliente.query
        .filter(func.lower(Cliente.nombre).like(f"%{q}%"))
        .order_by(Cliente.nombre.asc())
        .limit(25)
        .all()
    )
    # El JS espera una lista directa y usa horas_mes solo a modo informativo.
    return jsonify([{'id': c.id, 'nombre': c.nombre, 'horas_mes': 0.0} for c in items]), 200


@app.route('/api/registro-rapido/estadisticas-hoy', methods=['GET'])
@login_required
def api_estadisticas_hoy():
    tid = session.get('trabajador_id')
    if not tid:
        return jsonify({'ok': False, 'error': 'No tienes un trabajador asociado'}), 200
    hoy = date.today()
    regs = RegistroHora.query.filter_by(trabajador_id=tid, fecha=hoy).all()
    horas_total = float(sum(r.horas for r in regs) or 0)
    top_cliente = None
    if regs:
        por = {}
        for r in regs:
            por[r.cliente_id] = por.get(r.cliente_id, 0) + float(r.horas or 0)
        if por:
            cid = sorted(por.items(), key=lambda x: x[1], reverse=True)[0][0]
            c = Cliente.query.get(cid)
            top_cliente = c.nombre if c else None
    return jsonify({
        'ok': True,
        'horas_hoy': horas_total,
        'cliente_top': top_cliente,
        'alerta_8h': horas_total >= 8.0,
    }), 200


@app.route('/api/registro-rapido/historial', methods=['GET'])
@login_required
def api_historial():
    tid = session.get('trabajador_id')
    if not tid:
        return jsonify({'registros': [], 'error': 'No tienes un trabajador asociado'}), 200
    periodo = (request.args.get('periodo') or 'hoy').strip()
    cliente_id = request.args.get('cliente_id', type=int)
    hoy = date.today()
    if periodo == 'semana':
        desde = hoy - timedelta(days=hoy.weekday())
    elif periodo == 'mes':
        desde = date(hoy.year, hoy.month, 1)
    else:
        desde = hoy
    q = RegistroHora.query.filter(
        RegistroHora.trabajador_id == tid,
        RegistroHora.fecha >= desde,
        RegistroHora.fecha <= hoy,
    )
    if cliente_id:
        q = q.filter(RegistroHora.cliente_id == cliente_id)
    regs = q.order_by(RegistroHora.fecha.desc(), RegistroHora.id.desc()).limit(60).all()
    registros = [{
        'fecha': r.fecha.strftime('%Y-%m-%d'),
        'cliente': r.cliente.nombre if r.cliente else '',
        'tarea': r.tarea.nombre if r.tarea else '',
        'horas': float(r.horas or 0),
        'observaciones': r.observaciones or '',
    } for r in regs]
    return jsonify({'registros': registros}), 200


@app.route('/api/registro-rapido/guardar', methods=['POST'])
@login_required
def api_horas_guardar_rapido():
    payload = request.get_json(silent=True) or {}
    cliente_id = int(payload.get('cliente_id') or 0)
    tarea_id = int(payload.get('tarea_id') or 0)
    fecha_str = (payload.get('fecha') or date.today().strftime('%Y-%m-%d')).strip()
    horas_val = payload.get('horas')
    preset_min = payload.get('preset_minutos')
    observaciones = (payload.get('observaciones') or '').strip()
    if not (cliente_id and tarea_id and fecha_str and (horas_val is not None or preset_min is not None)):
        return jsonify({'ok': False, 'error': 'Faltan datos'}), 400

    if session.get('rol') == 'ADMIN' and payload.get('trabajador_id'):
        trabajador_id = int(payload.get('trabajador_id'))
    else:
        trabajador_id = session.get('trabajador_id')
    if not trabajador_id:
        return jsonify({'ok': False, 'error': 'No tienes un trabajador asociado'}), 400

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        if preset_min is not None and str(preset_min).isdigit():
            horas_trab = Decimal(str(int(preset_min))) / Decimal('60')
        else:
            horas_trab = Decimal(str(horas_val).replace(',', '.'))
    except Exception:
        return jsonify({'ok': False, 'error': 'Formato inválido'}), 400
    if horas_trab <= 0:
        return jsonify({'ok': False, 'error': 'Horas debe ser > 0'}), 400

    trabajador = Trabajador.query.get(trabajador_id)
    tarea = Tarea.query.get(tarea_id)
    cliente = Cliente.query.get(cliente_id)
    if not trabajador or not tarea or not cliente:
        return jsonify({'ok': False, 'error': 'Cliente/Tarea/Trabajador no válido'}), 400

    coste_total = horas_trab * trabajador.coste_hora
    clasificacion, importe_facturable, importe_manual = calcular_clasificacion_facturacion(tarea, cliente, horas_trab, trabajador)
    importe_facturar = importe_facturable if importe_facturable else Decimal(0)

    reg = RegistroHora(
        trabajador_id=trabajador_id,
        cliente_id=cliente_id,
        tarea_id=tarea_id,
        fecha=fecha,
        horas=horas_trab,
        coste_total=coste_total,
        importe_facturar=importe_facturar,
        clasificacion_facturacion=clasificacion,
        importe_facturable=importe_facturable,
        importe_manual=importe_manual,
        observaciones=observaciones if observaciones else None,
    )
    db.session.add(reg)
    db.session.commit()
    # Total hoy para avisos/estadísticas
    hoy = date.today()
    regs_hoy = RegistroHora.query.filter_by(trabajador_id=trabajador_id, fecha=hoy).all()
    horas_hoy = float(sum(r.horas for r in regs_hoy) or 0)
    return jsonify({
        'ok': True,
        'id': reg.id,
        'mensaje': 'Horas registradas',
        'horas_hoy': horas_hoy,
        'alerta_8h': horas_hoy >= 8.0,
    }), 200


@app.route('/api/timer/iniciar', methods=['POST'])
@login_required
def api_timer_iniciar():
    tid = session.get('trabajador_id')
    if not tid:
        return jsonify({'ok': False, 'error': 'No tienes un trabajador asociado'}), 400
    payload = request.get_json(silent=True) or {}
    cliente_id = int(payload.get('cliente_id') or 0)
    tarea_id = int(payload.get('tarea_id') or 0)
    nota = (payload.get('nota') or '').strip()
    if not cliente_id or not tarea_id:
        return jsonify({'ok': False, 'error': 'Falta cliente o tarea'}), 400

    existente = TimerTrabajo.query.filter_by(trabajador_id=tid).first()
    if existente:
        db.session.delete(existente)
        db.session.commit()

    t = TimerTrabajo(
        trabajador_id=tid,
        cliente_id=cliente_id,
        tarea_id=tarea_id,
        nota=nota if nota else None,
        started_at=datetime.now(),
        accumulated_seconds=0,
        is_paused=False,
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({'ok': True}), 200


@app.route('/api/timer/pausar', methods=['POST'])
@login_required
def api_timer_pausar():
    tid = session.get('trabajador_id')
    t = TimerTrabajo.query.filter_by(trabajador_id=tid).first() if tid else None
    if not t:
        return jsonify({'ok': False, 'error': 'No hay temporizador activo'}), 400
    if not t.is_paused and t.started_at:
        t.accumulated_seconds = int(t.accumulated_seconds or 0) + max(0, int((datetime.now() - t.started_at).total_seconds()))
    t.is_paused = True
    t.started_at = datetime.now()
    db.session.commit()
    return jsonify({'ok': True}), 200


@app.route('/api/timer/reanudar', methods=['POST'])
@login_required
def api_timer_reanudar():
    tid = session.get('trabajador_id')
    t = TimerTrabajo.query.filter_by(trabajador_id=tid).first() if tid else None
    if not t:
        return jsonify({'ok': False, 'error': 'No hay temporizador activo'}), 400
    t.is_paused = False
    t.started_at = datetime.now()
    db.session.commit()
    return jsonify({'ok': True}), 200


@app.route('/api/timer/cancelar', methods=['POST'])
@login_required
def api_timer_cancelar():
    tid = session.get('trabajador_id')
    t = TimerTrabajo.query.filter_by(trabajador_id=tid).first() if tid else None
    if t:
        db.session.delete(t)
        db.session.commit()
    return jsonify({'ok': True}), 200


@app.route('/api/timer/finalizar', methods=['POST'])
@login_required
def api_timer_finalizar():
    tid = session.get('trabajador_id')
    if not tid:
        return jsonify({'ok': False, 'error': 'No tienes un trabajador asociado'}), 400
    t = TimerTrabajo.query.filter_by(trabajador_id=tid).first()
    if not t:
        return jsonify({'ok': False, 'error': 'No hay temporizador activo'}), 400

    payload = request.get_json(silent=True) or {}
    redondeo = payload.get('redondeo')
    redondeo_min = payload.get('redondeo_min')
    ahora = datetime.now()
    segundos = int(t.accumulated_seconds or 0)
    if not t.is_paused and t.started_at:
        segundos += max(0, int((ahora - t.started_at).total_seconds()))
    minutos = max(0, int(round(segundos / 60)))
    # Compatibilidad con JS: {redondeo: "15"|"30"|...|""}
    if redondeo is not None and str(redondeo).isdigit():
        redondeo_min = int(redondeo)
    if redondeo_min in (15, 30, 60, 120):
        minutos = int(redondeo_min)
    horas_trab = Decimal(str(minutos)) / Decimal('60')

    trabajador = Trabajador.query.get(tid)
    tarea = Tarea.query.get(t.tarea_id)
    cliente = Cliente.query.get(t.cliente_id)
    if not trabajador or not tarea or not cliente:
        return jsonify({'ok': False, 'error': 'Cliente/Tarea no válido'}), 400

    coste_total = horas_trab * trabajador.coste_hora
    clasificacion, importe_facturable, importe_manual = calcular_clasificacion_facturacion(tarea, cliente, horas_trab, trabajador)
    importe_facturar = importe_facturable if importe_facturable else Decimal(0)
    reg = RegistroHora(
        trabajador_id=tid,
        cliente_id=t.cliente_id,
        tarea_id=t.tarea_id,
        fecha=date.today(),
        horas=horas_trab,
        coste_total=coste_total,
        importe_facturar=importe_facturar,
        clasificacion_facturacion=clasificacion,
        importe_facturable=importe_facturable,
        importe_manual=importe_manual,
        observaciones=(t.nota or None),
    )
    db.session.add(reg)
    db.session.delete(t)
    db.session.commit()
    # Total hoy para notificaciones
    hoy = date.today()
    regs_hoy = RegistroHora.query.filter_by(trabajador_id=tid, fecha=hoy).all()
    horas_hoy = float(sum(r.horas for r in regs_hoy) or 0)
    return jsonify({
        'ok': True,
        'registro_id': reg.id,
        'horas': float(horas_trab),
        'horas_hoy': horas_hoy,
        'alerta_8h': horas_hoy >= 8.0,
    }), 200

@app.route('/horas/nuevo', methods=['GET', 'POST'])
@login_required
def hora_nuevo():
    if request.method == 'POST':
        cliente_id = int(request.form.get('cliente_id'))
        tarea_id = int(request.form.get('tarea_id'))
        fecha_str = request.form.get('fecha')
        horas_trabajadas = Decimal(request.form.get('horas'))
        
        if session.get('rol') == 'ADMIN':
            trabajador_id = int(request.form.get('trabajador_id'))
        else:
            trabajador_id = session.get('trabajador_id')
            if not trabajador_id:
                flash('No tienes un trabajador asociado', 'error')
                return redirect(url_for('horas'))
        
        trabajador = Trabajador.query.get(trabajador_id)
        tarea = Tarea.query.get(tarea_id)
        cliente = Cliente.query.get(cliente_id)
        
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # Cálculos usando nuevo sistema
        coste_total = horas_trabajadas * trabajador.coste_hora
        clasificacion, importe_facturable, importe_manual = calcular_clasificacion_facturacion(tarea, cliente, horas_trabajadas, trabajador)
        
        # Mantener compatibilidad con campo antiguo
        importe_facturar = importe_facturable if importe_facturable else Decimal(0)
        
        registro = RegistroHora(
            trabajador_id=trabajador_id,
            cliente_id=cliente_id,
            tarea_id=tarea_id,
            fecha=fecha,
            horas=horas_trabajadas,
            coste_total=coste_total,
            importe_facturar=importe_facturar,
            clasificacion_facturacion=clasificacion,
            importe_facturable=importe_facturable,
            importe_manual=importe_manual
        )
        
        db.session.add(registro)
        db.session.commit()
        flash('Horas registradas correctamente', 'success')
        return redirect(url_for('horas'))
    
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    tareas = Tarea.query.order_by(Tarea.nombre).all()
    trabajadores = []
    if session.get('rol') == 'ADMIN':
        trabajadores = Trabajador.query.order_by(Trabajador.nombre).all()
    
    return render_template('hora_form.html', clientes=clientes, tareas=tareas, trabajadores=trabajadores)

@app.route('/horas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def hora_editar(id):
    registro = RegistroHora.query.get_or_404(id)
    
    # Verificar permisos
    if session.get('rol') != 'ADMIN' and registro.trabajador_id != session.get('trabajador_id'):
        flash('No tienes permiso para editar este registro', 'error')
        return redirect(url_for('horas'))
    
    if request.method == 'POST':
        cliente_id = int(request.form.get('cliente_id'))
        tarea_id = int(request.form.get('tarea_id'))
        fecha_str = request.form.get('fecha')
        horas_trabajadas = Decimal(request.form.get('horas'))
        
        if session.get('rol') == 'ADMIN':
            trabajador_id = int(request.form.get('trabajador_id'))
        else:
            trabajador_id = registro.trabajador_id
        
        trabajador = Trabajador.query.get(trabajador_id)
        tarea = Tarea.query.get(tarea_id)
        cliente = Cliente.query.get(cliente_id)
        
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # Recalcular usando nuevo sistema
        coste_total = horas_trabajadas * trabajador.coste_hora
        clasificacion, importe_facturable, importe_manual = calcular_clasificacion_facturacion(tarea, cliente, horas_trabajadas, trabajador)
        
        # Mantener compatibilidad con campo antiguo
        importe_facturar = importe_facturable if importe_facturable else Decimal(0)
        
        registro.trabajador_id = trabajador_id
        registro.cliente_id = cliente_id
        registro.tarea_id = tarea_id
        registro.fecha = fecha
        registro.horas = horas_trabajadas
        registro.coste_total = coste_total
        registro.importe_facturar = importe_facturar
        registro.clasificacion_facturacion = clasificacion
        registro.importe_facturable = importe_facturable
        registro.importe_manual = importe_manual
        
        db.session.commit()
        flash('Registro actualizado correctamente', 'success')
        return redirect(url_for('horas'))
    
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    tareas = Tarea.query.order_by(Tarea.nombre).all()
    trabajadores = []
    if session.get('rol') == 'ADMIN':
        trabajadores = Trabajador.query.order_by(Trabajador.nombre).all()
    
    return render_template('hora_form.html', registro=registro, clientes=clientes, tareas=tareas, trabajadores=trabajadores)

@app.route('/horas/eliminar/<int:id>', methods=['POST'])
@login_required
def hora_eliminar(id):
    registro = RegistroHora.query.get_or_404(id)
    
    # Verificar permisos
    if session.get('rol') != 'ADMIN' and registro.trabajador_id != session.get('trabajador_id'):
        flash('No tienes permiso para eliminar este registro', 'error')
        return redirect(url_for('horas'))
    
    db.session.delete(registro)
    db.session.commit()
    flash('Registro eliminado correctamente', 'success')
    return redirect(url_for('horas'))


def _lunes_de_semana(d):
    """Devuelve el lunes de la semana a la que pertenece la fecha d."""
    if isinstance(d, str):
        d = datetime.strptime(d, '%Y-%m-%d').date()
    return d - timedelta(days=d.weekday())


def _parse_hhmm(s):
    """Convierte 'H:MM' o 'H.MM' a Decimal horas. Ej: '1:30' -> 1.5."""
    if not s or not str(s).strip():
        return Decimal('0')
    s = str(s).strip().replace(',', '.')
    parts = s.replace(':', ' ').split()
    h = Decimal(parts[0]) if len(parts) > 0 and parts[0] else Decimal('0')
    m = Decimal(parts[1]) if len(parts) > 1 and parts[1] else Decimal('0')
    return h + m / 60


def _decimal_a_hhmm(d):
    """Convierte Decimal horas a string 'H:MM'. Ej: 1.5 -> '1:30'."""
    if d is None or d <= 0:
        return '0:00'
    h = int(d)
    m = round(float((d - h) * 60))
    if m >= 60:
        h += 1
        m = 0
    return f"{h}:{m:02d}"


@app.route('/horas/semana')
@login_required
def horas_semana():
    """Registro semanal: semana actual por defecto, contador hoy/semana, prefill si tarea+cliente."""
    semana_param = request.args.get('semana')
    tarea_id_param = request.args.get('tarea_id', type=int)
    cliente_id_param = request.args.get('cliente_id', type=int)
    hoy = date.today()
    lunes = _lunes_de_semana(semana_param if semana_param else hoy)
    lunes_str = lunes.strftime('%Y-%m-%d')
    dias_semana = ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo')
    fechas = [lunes + timedelta(days=i) for i in range(7)]
    fechas_str = [f.strftime('%Y-%m-%d') for f in fechas]

    trabajador_id = session.get('trabajador_id')
    if not trabajador_id and session.get('rol') == 'ADMIN':
        trabajador_id = request.args.get('trabajador_id', type=int)
    horas_hoy = Decimal('0')
    horas_semana_total = Decimal('0')
    if trabajador_id:
        registros_hoy = RegistroHora.query.filter(
            RegistroHora.trabajador_id == trabajador_id,
            RegistroHora.fecha == hoy
        ).all()
        horas_hoy = sum(r.horas for r in registros_hoy)
        registros_semana = RegistroHora.query.filter(
            RegistroHora.trabajador_id == trabajador_id,
            RegistroHora.fecha >= lunes,
            RegistroHora.fecha <= fechas[-1]
        ).all()
        horas_semana_total = sum(r.horas for r in registros_semana)

    clientes = Cliente.query.order_by(Cliente.nombre).all()
    tareas = Tarea.query.order_by(Tarea.nombre).all()
    trabajadores = Trabajador.query.order_by(Trabajador.nombre).all() if session.get('rol') == 'ADMIN' else []

    horas_prefill = [''] * 7
    obs_prefill = [''] * 7
    if tarea_id_param and cliente_id_param and trabajador_id:
        for i in range(7):
            fd = fechas[i]
            r = RegistroHora.query.filter_by(
                trabajador_id=trabajador_id,
                tarea_id=tarea_id_param,
                cliente_id=cliente_id_param,
                fecha=fd
            ).first()
            if r:
                horas_prefill[i] = _decimal_a_hhmm(r.horas)
                obs_prefill[i] = r.observaciones or ''

    return render_template(
        'horas_semana.html',
        lunes_str=lunes_str,
        dias_semana=dias_semana,
        fechas_str=fechas_str,
        horas_prefill=horas_prefill,
        obs_prefill=obs_prefill,
        clientes=clientes,
        tareas=tareas,
        trabajadores=trabajadores,
        horas_hoy=horas_hoy,
        horas_semana_total=horas_semana_total,
        tarea_id_param=tarea_id_param,
        cliente_id_param=cliente_id_param,
    )


@app.route('/horas/semana/guardar', methods=['POST'])
@login_required
def horas_semana_guardar():
    """Guarda/actualiza registros por día: si existe registro para ese día+tarea+cliente, actualizar; si no, crear."""
    lunes_str = request.form.get('semana')
    if not lunes_str:
        flash('Falta la fecha de la semana', 'error')
        return redirect(url_for('horas_semana'))
    lunes = datetime.strptime(lunes_str, '%Y-%m-%d').date()
    cliente_id = request.form.get('cliente_id', type=int)
    tarea_id = request.form.get('tarea_id', type=int)
    if not cliente_id or not tarea_id:
        flash('Seleccione cliente y tarea', 'error')
        return redirect(url_for('horas_semana', semana=lunes_str))
    if session.get('rol') == 'ADMIN':
        trabajador_id = request.form.get('trabajador_id', type=int)
    else:
        trabajador_id = session.get('trabajador_id')
    if not trabajador_id:
        flash('No tienes un trabajador asociado', 'error')
        return redirect(url_for('horas'))
    trabajador = Trabajador.query.get(trabajador_id)
    tarea = Tarea.query.get(tarea_id)
    cliente = Cliente.query.get(cliente_id)
    actualizados = 0
    creados = 0
    for i in range(7):
        fecha_d = lunes + timedelta(days=i)
        horas_val = request.form.get('horas_' + str(i), '')
        obs_val = request.form.get('obs_' + str(i), '').strip()
        h = _parse_hhmm(horas_val)
        registro = RegistroHora.query.filter_by(
            trabajador_id=trabajador_id,
            tarea_id=tarea_id,
            cliente_id=cliente_id,
            fecha=fecha_d,
        ).first()
        if h > 0:
            coste_total = h * trabajador.coste_hora
            clasificacion, importe_facturable, importe_manual = calcular_clasificacion_facturacion(tarea, cliente, h, trabajador)
            importe_facturar = importe_facturable if importe_facturable else Decimal(0)
            if registro:
                registro.horas = h
                registro.coste_total = coste_total
                registro.importe_facturar = importe_facturar
                registro.clasificacion_facturacion = clasificacion
                registro.importe_facturable = importe_facturable
                registro.importe_manual = importe_manual
                registro.observaciones = obs_val if obs_val else None
                actualizados += 1
            else:
                nuevo = RegistroHora(
                    trabajador_id=trabajador_id,
                    cliente_id=cliente_id,
                    tarea_id=tarea_id,
                    fecha=fecha_d,
                    horas=h,
                    coste_total=coste_total,
                    importe_facturar=importe_facturar,
                    clasificacion_facturacion=clasificacion,
                    importe_facturable=importe_facturable,
                    importe_manual=importe_manual,
                    observaciones=obs_val if obs_val else None,
                )
                db.session.add(nuevo)
                creados += 1
            db.session.commit()
        elif registro:
            db.session.delete(registro)
            db.session.commit()
    msg = []
    if creados:
        msg.append(f'{creados} nuevo(s)')
    if actualizados:
        msg.append(f'{actualizados} actualizado(s)')
    flash('Horas de la semana guardadas correctamente.' + (' ' + ', '.join(msg)) if msg else '', 'success')
    return redirect(url_for('horas_semana', semana=lunes_str, tarea_id=tarea_id, cliente_id=cliente_id))


@app.route('/horas/guardar-dia', methods=['POST'])
@login_required
def guardar_dia_individual():
    """Guarda un solo día: crear, actualizar o eliminar según las horas."""
    fecha_str = request.form.get('fecha')
    tarea_id = request.form.get('tarea_id', type=int)
    cliente_id = request.form.get('cliente_id', type=int)
    horas_input = request.form.get('horas', '')
    observaciones = request.form.get('observaciones', '').strip()
    
    if not fecha_str or not tarea_id or not cliente_id:
        return jsonify({'success': False, 'error': 'Faltan datos requeridos'}), 400
    
    if session.get('rol') == 'ADMIN':
        trabajador_id = request.form.get('trabajador_id', type=int)
    else:
        trabajador_id = session.get('trabajador_id')
    
    if not trabajador_id:
        return jsonify({'success': False, 'error': 'No tienes un trabajador asociado'}), 400
    
    fecha_d = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    h = _parse_hhmm(horas_input)
    
    registro = RegistroHora.query.filter_by(
        trabajador_id=trabajador_id,
        tarea_id=tarea_id,
        cliente_id=cliente_id,
        fecha=fecha_d,
    ).first()
    
    trabajador = Trabajador.query.get(trabajador_id)
    tarea = Tarea.query.get(tarea_id)
    cliente = Cliente.query.get(cliente_id)
    
    if h == 0:
        if registro:
            db.session.delete(registro)
            db.session.commit()
            return jsonify({
                'success': True,
                'accion': 'eliminado',
                'mensaje': 'Registro eliminado'
            })
        else:
            return jsonify({
                'success': True,
                'accion': 'sin_cambios',
                'mensaje': 'No hay registro para eliminar'
            })
    
    coste_total = h * trabajador.coste_hora
    clasificacion, importe_facturable, importe_manual = calcular_clasificacion_facturacion(tarea, cliente, h, trabajador)
    importe_facturar = importe_facturable if importe_facturable else Decimal(0)
    
    if registro:
        registro.horas = h
        registro.coste_total = coste_total
        registro.importe_facturar = importe_facturar
        registro.clasificacion_facturacion = clasificacion
        registro.importe_facturable = importe_facturable
        registro.importe_manual = importe_manual
        registro.observaciones = observaciones if observaciones else None
        accion = 'actualizado'
    else:
        registro = RegistroHora(
            trabajador_id=trabajador_id,
            cliente_id=cliente_id,
            tarea_id=tarea_id,
            fecha=fecha_d,
            horas=h,
            coste_total=coste_total,
            importe_facturar=importe_facturar,
            clasificacion_facturacion=clasificacion,
            importe_facturable=importe_facturable,
            importe_manual=importe_manual,
            observaciones=observaciones if observaciones else None,
        )
        db.session.add(registro)
        accion = 'creado'
    
    db.session.commit()
    
    hoy = date.today()
    horas_hoy = Decimal('0')
    horas_semana_total = Decimal('0')
    lunes = fecha_d - timedelta(days=fecha_d.weekday())
    domingo = lunes + timedelta(days=6)
    
    registros_hoy = RegistroHora.query.filter(
        RegistroHora.trabajador_id == trabajador_id,
        RegistroHora.fecha == hoy
    ).all()
    horas_hoy = sum(r.horas for r in registros_hoy)
    
    registros_semana = RegistroHora.query.filter(
        RegistroHora.trabajador_id == trabajador_id,
        RegistroHora.fecha >= lunes,
        RegistroHora.fecha <= domingo
    ).all()
    horas_semana_total = sum(r.horas for r in registros_semana)
    
    return jsonify({
        'success': True,
        'accion': accion,
        'mensaje': f'Registro {accion} correctamente',
        'horas_hoy': float(horas_hoy),
        'horas_semana': float(horas_semana_total)
    })


# ==================== INFORMES ====================

@app.route('/informe')
@admin_required
def informe():
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    ahora = datetime.now()
    return render_template('informe.html', clientes=clientes, mes_actual=ahora.month, año_actual=ahora.year)

@app.route('/informe/generar', methods=['POST'])
@admin_required
def informe_generar():
    cliente_id = int(request.form.get('cliente_id'))
    mes = int(request.form.get('mes'))
    año = int(request.form.get('año'))
    
    cliente = Cliente.query.get_or_404(cliente_id)
    
    # Filtrar registros del mes
    inicio_mes = date(año, mes, 1)
    if mes == 12:
        fin_mes = date(año + 1, 1, 1)
    else:
        fin_mes = date(año, mes + 1, 1)
    
    registros = RegistroHora.query.filter(
        and_(
            RegistroHora.cliente_id == cliente_id,
            RegistroHora.fecha >= inicio_mes,
            RegistroHora.fecha < fin_mes
        )
    ).all()
    
    # Servicios facturables: solo FACTURABLE, LIMITE_SUPERADO, TARIFA_MANUAL (para informe a facturación)
    tareas_fuera_contrato = [r for r in registros if r.clasificacion_facturacion in ('FACTURABLE', 'LIMITE_SUPERADO', 'TARIFA_MANUAL')]
    
    # Coste interno total (solo control de costes; NO se calculan ingresos ni rentabilidad)
    coste_total = sum(r.coste_total for r in registros)
    
    # Resumen por trabajador
    horas_por_trabajador = {}
    for r in registros:
        if r.trabajador.nombre not in horas_por_trabajador:
            horas_por_trabajador[r.trabajador.nombre] = 0
        horas_por_trabajador[r.trabajador.nombre] += float(r.horas)
    
    # Resumen por tarea
    horas_por_tarea = {}
    for r in registros:
        if r.tarea.nombre not in horas_por_tarea:
            horas_por_tarea[r.tarea.nombre] = 0
        horas_por_tarea[r.tarea.nombre] += float(r.horas)
    
    # Crear Excel
    wb = Workbook()
    ws = wb.active
    # Excel no permite caracteres especiales como / en nombres de hojas
    ws.title = f"Informe {mes}-{año}"
    
    # Estilos
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    # Encabezado
    ws['A1'] = f"INFORME MENSUAL - {cliente.nombre.upper()}"
    ws['A1'].font = Font(bold=True, size=14)
    ws.merge_cells('A1:E1')
    ws['A2'] = f"Período: {mes}/{año}"
    ws.merge_cells('A2:E2')
    
    row = 4
    
    # 1. Tareas fuera de contrato
    ws[f'A{row}'] = "TAREAS NO INCLUIDAS EN CONTRATO"
    ws[f'A{row}'].font = header_font
    ws[f'A{row}'].fill = header_fill
    ws.merge_cells(f'A{row}:E{row}')
    row += 1
    
    ws[f'A{row}'] = "Tarea"
    ws[f'B{row}'] = "Trabajador"
    ws[f'C{row}'] = "Horas"
    ws[f'D{row}'] = "Importe"
    for col in ['A', 'B', 'C', 'D']:
        ws[f'{col}{row}'].font = header_font
        ws[f'{col}{row}'].fill = header_fill
    
    row += 1
    primera_fila = row
    for r in tareas_fuera_contrato:
        ws[f'A{row}'] = r.tarea.nombre
        ws[f'B{row}'] = r.trabajador.nombre
        ws[f'C{row}'] = float(r.horas)
        ws[f'D{row}'] = float(r.importe_facturar)
        row += 1
    
    if tareas_fuera_contrato:
        ws[f'C{row}'] = f"=SUM(C{primera_fila}:C{row-1})"
        ws[f'D{row}'] = f"=SUM(D{primera_fila}:D{row-1})"
        ws[f'C{row}'].font = Font(bold=True)
        ws[f'D{row}'].font = Font(bold=True)
        row += 1
    else:
        ws[f'A{row}'] = "No hay tareas fuera de contrato en este período"
        ws.merge_cells(f'A{row}:D{row}')
        row += 1
    
    row += 2
    
    # 2. Coste interno (solo control de costes; no se usa para ingresos ni rentabilidad)
    ws[f'A{row}'] = "COSTE INTERNO DEL MES"
    ws[f'A{row}'].font = header_font
    ws[f'A{row}'].fill = header_fill
    ws.merge_cells(f'A{row}:B{row}')
    row += 1
    ws[f'A{row}'] = "Coste total de horas trabajadas (suma de horas x coste_hora por trabajador):"
    ws[f'B{row}'] = float(coste_total)
    ws[f'A{row}'].font = Font(bold=True)
    ws[f'B{row}'].font = Font(bold=True)
    row += 2
    
    # 3. Resumen de horas
    ws[f'A{row}'] = "RESUMEN DE HORAS POR TRABAJADOR"
    ws[f'A{row}'].font = header_font
    ws[f'A{row}'].fill = header_fill
    ws.merge_cells(f'A{row}:B{row}')
    row += 1
    
    ws[f'A{row}'] = "Trabajador"
    ws[f'B{row}'] = "Horas"
    for col in ['A', 'B']:
        ws[f'{col}{row}'].font = header_font
        ws[f'{col}{row}'].fill = header_fill
    row += 1
    
    for trabajador, horas in sorted(horas_por_trabajador.items()):
        ws[f'A{row}'] = trabajador
        ws[f'B{row}'] = horas
        row += 1
    
    row += 1
    
    ws[f'A{row}'] = "RESUMEN DE HORAS POR TAREA"
    ws[f'A{row}'].font = header_font
    ws[f'A{row}'].fill = header_fill
    ws.merge_cells(f'A{row}:B{row}')
    row += 1
    
    ws[f'A{row}'] = "Tarea"
    ws[f'B{row}'] = "Horas"
    for col in ['A', 'B']:
        ws[f'{col}{row}'].font = header_font
        ws[f'{col}{row}'].fill = header_fill
    row += 1
    
    for tarea, horas in sorted(horas_por_tarea.items()):
        ws[f'A{row}'] = tarea
        ws[f'B{row}'] = horas
        row += 1
    
    # Ajustar ancho de columnas
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 15
    
    # Guardar archivo
    filename = f"informe_{cliente.nombre.replace(' ', '_')}_{mes}_{año}.xlsx"
    filepath = os.path.join('temp', filename)
    os.makedirs('temp', exist_ok=True)
    wb.save(filepath)
    
    return send_file(filepath, as_attachment=True, download_name=filename)


# ---------- Helpers para informes ----------
def _rango_mes(mes, año):
    inicio_mes = date(año, mes, 1)
    if mes == 12:
        fin_mes = date(año + 1, 1, 1)
    else:
        fin_mes = date(año, mes + 1, 1)
    return inicio_mes, fin_mes


def _horas_acumulado_anio(anio, hasta_mes, trabajador_ids=None):
    """Devuelve el total de horas desde 1 de enero hasta fin de hasta_mes (inclusive) del año. Sin coste."""
    inicio_anio = date(anio, 1, 1)
    if hasta_mes == 12:
        fin = date(anio + 1, 1, 1)
    else:
        fin = date(anio, hasta_mes + 1, 1)
    q = RegistroHora.query.filter(
        RegistroHora.fecha >= inicio_anio,
        RegistroHora.fecha < fin
    )
    if trabajador_ids is not None:
        q = q.filter(RegistroHora.trabajador_id.in_(trabajador_ids))
    registros = q.all()
    return sum(r.horas for r in registros)


def _es_facturable_para_informe(r):
    """Solo FACTURABLE, LIMITE_SUPERADO o TARIFA_MANUAL (con o sin importe) van a informes de facturación."""
    return r.clasificacion_facturacion in ('FACTURABLE', 'LIMITE_SUPERADO', 'TARIFA_MANUAL')


def _clasificacion_e_importe_actual(r):
    """
    Recalcula clasificación e importe con la configuración actual de tarea y cliente.
    Así el informe de facturación refleja la configuración actual aunque el registro
    se guardara con una clasificación antigua.
    Retorna: (clasificacion, importe_facturable, importe_manual)
    """
    clasif, imp_fact, imp_manual = calcular_clasificacion_facturacion(r.tarea, r.cliente, r.horas, r.trabajador)
    if clasif == 'TARIFA_MANUAL' and (imp_manual is None or imp_manual == 0) and r.importe_manual is not None:
        imp_manual = r.importe_manual
    return clasif, imp_fact or Decimal('0'), imp_manual


def _importe_facturable_registro(r):
    """Importe a facturar: importe_facturable, importe_manual o importe_facturar."""
    if r.importe_manual is not None:
        return r.importe_manual
    if r.importe_facturable is not None:
        return r.importe_facturable
    return r.importe_facturar or Decimal('0')


# ==================== INFORME 1: COSTES INTERNOS (TODOS LOS CLIENTES) ====================

@app.route('/informes/costes-internos/<int:mes>/<int:anio>')
@admin_required
def informe_costes_internos(mes, anio):
    inicio_mes, fin_mes = _rango_mes(mes, anio)
    trabajadores = Trabajador.query.order_by(Trabajador.nombre).all()
    clientes = Cliente.query.order_by(Cliente.nombre).all()

    registros = RegistroHora.query.filter(
        and_(
            RegistroHora.fecha >= inicio_mes,
            RegistroHora.fecha < fin_mes
        )
    ).all()

    # Una fila por cada cliente (todos), con 0 si no hay registros en el mes
    filas = []
    for cliente in clientes:
        regs_cliente = [r for r in registros if r.cliente_id == cliente.id]
        horas_por_trab = {}
        coste_interno = Decimal('0')
        servicios_fuera_cuota = Decimal('0')

        for r in regs_cliente:
            horas_por_trab[r.trabajador.nombre] = horas_por_trab.get(r.trabajador.nombre, Decimal('0')) + r.horas
            coste_interno += r.coste_total
            if _es_facturable_para_informe(r):
                servicios_fuera_cuota += _importe_facturable_registro(r)

        filas.append({
            'cliente': cliente,
            'horas_por_trabajador': horas_por_trab,
            'coste_interno_total': coste_interno,
            'servicios_fuera_cuota': servicios_fuera_cuota,
        })

    # Totales para el pie de tabla
    totales_horas = {t.nombre: sum(f['horas_por_trabajador'].get(t.nombre, 0) for f in filas) for t in trabajadores}
    total_coste = sum(f['coste_interno_total'] for f in filas)
    total_servicios = sum(f['servicios_fuera_cuota'] for f in filas)

    nombres_meses = ('', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre')
    return render_template(
        'informe_costes_internos.html',
        filas=filas,
        trabajadores=trabajadores,
        totales_horas=totales_horas,
        total_coste=total_coste,
        total_servicios=total_servicios,
        mes=mes,
        año=anio,
        nombre_mes=nombres_meses[mes] if 1 <= mes <= 12 else str(mes)
    )


@app.route('/informes/costes-internos/<int:mes>/<int:anio>/excel')
@admin_required
def informe_costes_internos_excel(mes, anio):
    inicio_mes, fin_mes = _rango_mes(mes, anio)
    trabajadores = Trabajador.query.order_by(Trabajador.nombre).all()
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    registros = RegistroHora.query.filter(
        and_(RegistroHora.fecha >= inicio_mes, RegistroHora.fecha < fin_mes)
    ).all()

    wb = Workbook()
    ws = wb.active
    ws.title = f"Costes {mes}-{anio}"
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    # Cabecera: Cliente | Trab1 | Trab2 | ... | COSTE INTERNO | SERVICIOS FUERA CUOTA
    ws.cell(row=1, column=1, value="Cliente")
    for c, t in enumerate(trabajadores, start=2):
        ws.cell(row=1, column=c, value=t.nombre)
    col_coste = len(trabajadores) + 2
    col_servicios = len(trabajadores) + 3
    ws.cell(row=1, column=col_coste, value="COSTE INTERNO TOTAL")
    ws.cell(row=1, column=col_servicios, value="SERVICIOS FUERA CUOTA")
    for c in range(1, col_servicios + 1):
        ws.cell(row=1, column=c).font = header_font
        ws.cell(row=1, column=c).fill = header_fill

    row = 2
    totales_horas = {t.nombre: Decimal('0') for t in trabajadores}
    total_coste = Decimal('0')
    total_servicios = Decimal('0')

    for cliente in clientes:
        regs_cliente = [r for r in registros if r.cliente_id == cliente.id]
        horas_por_trab = {}
        coste_interno = Decimal('0')
        servicios_fuera_cuota = Decimal('0')
        for r in regs_cliente:
            horas_por_trab[r.trabajador.nombre] = horas_por_trab.get(r.trabajador.nombre, Decimal('0')) + r.horas
            coste_interno += r.coste_total
            if _es_facturable_para_informe(r):
                servicios_fuera_cuota += _importe_facturable_registro(r)

        ws.cell(row=row, column=1, value=cliente.nombre)
        for c, t in enumerate(trabajadores, start=2):
            h = horas_por_trab.get(t.nombre, Decimal('0'))
            ws.cell(row=row, column=c, value=float(h))
            totales_horas[t.nombre] += h
        ws.cell(row=row, column=col_coste, value=float(coste_interno))
        ws.cell(row=row, column=col_servicios, value=float(servicios_fuera_cuota))
        total_coste += coste_interno
        total_servicios += servicios_fuera_cuota
        row += 1

    # Fila totales
    ws.cell(row=row, column=1, value="TOTALES")
    ws.cell(row=row, column=1).font = Font(bold=True)
    for c, t in enumerate(trabajadores, start=2):
        ws.cell(row=row, column=c, value=float(totales_horas[t.nombre])).font = Font(bold=True)
    ws.cell(row=row, column=col_coste, value=float(total_coste)).font = Font(bold=True)
    ws.cell(row=row, column=col_servicios, value=float(total_servicios)).font = Font(bold=True)

    for c in range(1, col_servicios + 1):
        ws.column_dimensions[get_column_letter(c)].width = 14
    ws.column_dimensions['A'].width = 28

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"informe_costes_internos_{mes}_{anio}.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ==================== INFORME FINAL DE HORAS (Cliente | Horas por trabajador | Coste) ====================

@app.route('/informes/horas-final/<int:mes>/<int:anio>')
@admin_required
def informe_horas_final(mes, anio):
    """Informe final: Cliente, horas por trabajador (una columna cada uno), coste = suma(horas × coste_hora)."""
    inicio_mes, fin_mes = _rango_mes(mes, anio)
    trabajadores = Trabajador.query.order_by(Trabajador.nombre).all()
    clientes = Cliente.query.order_by(Cliente.nombre).all()

    registros = RegistroHora.query.filter(
        and_(
            RegistroHora.fecha >= inicio_mes,
            RegistroHora.fecha < fin_mes
        )
    ).all()

    filas = []
    for cliente in clientes:
        regs_cliente = [r for r in registros if r.cliente_id == cliente.id]
        horas_por_trab = {}
        coste = Decimal('0')
        for r in regs_cliente:
            horas_por_trab[r.trabajador.nombre] = horas_por_trab.get(r.trabajador.nombre, Decimal('0')) + r.horas
            coste += r.coste_total

        filas.append({
            'cliente': cliente,
            'horas_por_trabajador': horas_por_trab,
            'coste': coste,
        })

    totales_horas = {t.nombre: sum(f['horas_por_trabajador'].get(t.nombre, 0) for f in filas) for t in trabajadores}
    total_coste = sum(f['coste'] for f in filas)

    nombres_meses = ('', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre')
    return render_template(
        'informe_horas_final.html',
        filas=filas,
        trabajadores=trabajadores,
        totales_horas=totales_horas,
        total_coste=total_coste,
        mes=mes,
        año=anio,
        nombre_mes=nombres_meses[mes] if 1 <= mes <= 12 else str(mes)
    )


@app.route('/informes/horas-final/<int:mes>/<int:anio>/excel')
@admin_required
def informe_horas_final_excel(mes, anio):
    """Exporta el informe final de horas a Excel: Cliente | Horas trabajador | Coste."""
    inicio_mes, fin_mes = _rango_mes(mes, anio)
    trabajadores = Trabajador.query.order_by(Trabajador.nombre).all()
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    registros = RegistroHora.query.filter(
        and_(RegistroHora.fecha >= inicio_mes, RegistroHora.fecha < fin_mes)
    ).all()

    wb = Workbook()
    ws = wb.active
    ws.title = f"Horas final {mes}-{anio}"
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    # Cabecera: Cliente | Trab1 | Trab2 | ... | COSTE
    ws.cell(row=1, column=1, value="Cliente")
    for c, t in enumerate(trabajadores, start=2):
        ws.cell(row=1, column=c, value=t.nombre)
    col_coste = len(trabajadores) + 2
    ws.cell(row=1, column=col_coste, value="COSTE")
    for c in range(1, col_coste + 1):
        ws.cell(row=1, column=c).font = header_font
        ws.cell(row=1, column=c).fill = header_fill

    row = 2
    totales_horas = {t.nombre: Decimal('0') for t in trabajadores}
    total_coste = Decimal('0')

    for cliente in clientes:
        regs_cliente = [r for r in registros if r.cliente_id == cliente.id]
        horas_por_trab = {}
        coste = Decimal('0')
        for r in regs_cliente:
            horas_por_trab[r.trabajador.nombre] = horas_por_trab.get(r.trabajador.nombre, Decimal('0')) + r.horas
            coste += r.coste_total

        ws.cell(row=row, column=1, value=cliente.nombre)
        for c, t in enumerate(trabajadores, start=2):
            h = horas_por_trab.get(t.nombre, Decimal('0'))
            ws.cell(row=row, column=c, value=float(h))
            totales_horas[t.nombre] += h
        ws.cell(row=row, column=col_coste, value=float(coste))
        total_coste += coste
        row += 1

    # Fila totales
    ws.cell(row=row, column=1, value="TOTALES")
    ws.cell(row=row, column=1).font = Font(bold=True)
    for c, t in enumerate(trabajadores, start=2):
        ws.cell(row=row, column=c, value=float(totales_horas[t.nombre])).font = Font(bold=True)
    ws.cell(row=row, column=col_coste, value=float(total_coste)).font = Font(bold=True)

    for c in range(1, col_coste + 1):
        ws.column_dimensions[get_column_letter(c)].width = 14
    ws.column_dimensions['A'].width = 28

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"informe_horas_final_{mes}_{anio}.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ==================== INFORME 2: FACTURACIÓN MENSUAL (Admin y Trabajador - solo lectura para trabajador) ====================

@app.route('/informes/facturacion/<int:mes>/<int:anio>')
@facturacion_required
def informe_facturacion(mes, anio):
    cliente_id = request.args.get('cliente_id', type=int)
    inicio_mes, fin_mes = _rango_mes(mes, anio)
    clientes = Cliente.query.order_by(Cliente.nombre).all()

    registros = RegistroHora.query.filter(
        and_(
            RegistroHora.fecha >= inicio_mes,
            RegistroHora.fecha < fin_mes
        )
    ).all()

    # Usar clasificación actual (recalculada) para que el informe refleje la config actual de tarea/cliente
    registros_fact = []
    for r in registros:
        if r.tarea.tipo_tarea == 'INTERNA':
            continue
        clasif, imp_fact, imp_manual = _clasificacion_e_importe_actual(r)
        if clasif not in ('FACTURABLE', 'LIMITE_SUPERADO', 'TARIFA_MANUAL'):
            continue
        registros_fact.append((r, clasif, imp_fact, imp_manual))

    if cliente_id:
        registros_fact = [x for x in registros_fact if x[0].cliente_id == cliente_id]
        cliente_filtro = Cliente.query.get(cliente_id)
    else:
        cliente_filtro = None

    # Agrupar por cliente
    por_cliente = {}
    for r, clasif, imp_fact, imp_manual in registros_fact:
        cid = r.cliente_id
        if cid not in por_cliente:
            por_cliente[cid] = []
        por_cliente[cid].append((r, clasif, imp_fact, imp_manual))

    # Construir datos por cliente: cuota, líneas (concepto, detalle, importe), pendientes
    datos_clientes = []
    for cid, regs in por_cliente.items():
        cliente = Cliente.query.get(cid)
        cuota = cliente.precio_cuota_mensual or cliente.cuota_mensual or Decimal('0')
        lineas = []
        pendientes = 0
        for r, clasif, imp_fact, imp_manual in regs:
            if clasif == 'TARIFA_MANUAL':
                imp = r.importe_manual if (r.importe_manual is not None and r.importe_manual != 0) else (imp_manual if (imp_manual is not None and imp_manual != 0) else imp_fact)
            else:
                imp = imp_fact
            if imp is None:
                imp = Decimal('0')
            if clasif == 'TARIFA_MANUAL' and (imp is None or imp == 0) and (r.importe_manual is None or r.importe_manual == 0):
                detalle = f"{float(r.horas)}h trabajada(s)"
                importe_str = "PENDIENTE"
                importe_num = None
                pendientes += 1
            else:
                detalle = f"{float(r.horas)}h x {float(r.trabajador.coste_hora)}€/h"
                importe_str = f"{float(imp):.2f}€"
                importe_num = imp
            lineas.append({'concepto': r.tarea.nombre, 'detalle': detalle, 'importe_str': importe_str, 'importe_num': importe_num})
        subtotal = sum(l['importe_num'] for l in lineas if l.get('importe_num') is not None)
        total = cuota + subtotal
        datos_clientes.append({
            'cliente': cliente,
            'cuota_mensual': cuota,
            'lineas': lineas,
            'subtotal_extra': subtotal,
            'total_factura': total,
            'pendientes': pendientes,
        })

    nombres_meses = ('', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre')
    es_admin = session.get('rol') == 'ADMIN'
    return render_template(
        'informe_facturacion.html',
        datos_clientes=datos_clientes,
        clientes=clientes,
        cliente_filtro=cliente_filtro,
        mes=mes,
        año=anio,
        nombre_mes=nombres_meses[mes] if 1 <= mes <= 12 else str(mes),
        es_admin=es_admin,
    )


@app.route('/informes/facturacion/<int:mes>/<int:anio>/excel')
@facturacion_required
def informe_facturacion_excel(mes, anio):
    cliente_id = request.args.get('cliente_id', type=int)
    inicio_mes, fin_mes = _rango_mes(mes, anio)
    registros = RegistroHora.query.filter(
        and_(RegistroHora.fecha >= inicio_mes, RegistroHora.fecha < fin_mes)
    ).all()
    registros_fact = []
    for r in registros:
        if r.tarea.tipo_tarea == 'INTERNA':
            continue
        clasif, imp_fact, imp_manual = _clasificacion_e_importe_actual(r)
        if clasif not in ('FACTURABLE', 'LIMITE_SUPERADO', 'TARIFA_MANUAL'):
            continue
        registros_fact.append((r, clasif, imp_fact, imp_manual))
    if cliente_id:
        registros_fact = [x for x in registros_fact if x[0].cliente_id == cliente_id]

    por_cliente = {}
    for r, clasif, imp_fact, imp_manual in registros_fact:
        cid = r.cliente_id
        if cid not in por_cliente:
            por_cliente[cid] = []
        por_cliente[cid].append((r, clasif, imp_fact, imp_manual))

    wb = Workbook()
    header_font = Font(bold=True)
    for cid, regs in por_cliente.items():
        cliente = Cliente.query.get(cid)
        nombre_hoja = cliente.nombre[:31].replace('/', '-').replace('\\', '-').replace('*', '').replace('?', '').replace('[', '').replace(']', '')
        ws = wb.create_sheet(title=nombre_hoja)
        row = 1
        ws.cell(row=row, column=1, value=f"INFORME DE FACTURACIÓN - {mes}/{anio}")
        row += 1
        ws.cell(row=row, column=1, value=f"Cliente: {cliente.nombre}")
        row += 1
        ws.cell(row=row, column=1, value=f"Modalidad: {cliente.modalidad_cuota}")
        row += 2
        ws.cell(row=row, column=1, value="Concepto")
        ws.cell(row=row, column=2, value="Detalle")
        ws.cell(row=row, column=3, value="Importe")
        for col in range(1, 4):
            ws.cell(row=row, column=col).font = header_font
        row += 1
        subtotal = Decimal('0')
        for r, clasif, imp_fact, imp_manual in regs:
            if clasif == 'TARIFA_MANUAL':
                imp = r.importe_manual if (r.importe_manual is not None and r.importe_manual != 0) else (imp_manual if (imp_manual is not None and imp_manual != 0) else imp_fact)
            else:
                imp = imp_fact
            if imp is None:
                imp = Decimal('0')
            if clasif == 'TARIFA_MANUAL' and (imp is None or imp == 0) and (r.importe_manual is None or r.importe_manual == 0):
                detalle = f"{float(r.horas)}h"
                importe_str = "PENDIENTE"
            else:
                detalle = f"{float(r.horas)}h"
                importe_str = f"{float(imp):.2f}"
                subtotal += imp
            ws.cell(row=row, column=1, value=r.tarea.nombre)
            ws.cell(row=row, column=2, value=detalle)
            ws.cell(row=row, column=3, value=importe_str)
            row += 1
        row += 1
        ws.cell(row=row, column=1, value="TOTAL A FACTURAR")
        ws.cell(row=row, column=1).font = header_font
        ws.cell(row=row, column=3, value=float(subtotal)).font = header_font

    if por_cliente:
        wb.remove(wb.active)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"informe_facturacion_{mes}_{anio}.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route('/informes/facturacion/<int:mes>/<int:anio>/pdf')
@facturacion_required
def informe_facturacion_pdf(mes, anio):
    """Redirige a la vista HTML imprimible (el usuario puede usar Imprimir > Guardar como PDF)."""
    return redirect(url_for('informe_facturacion', mes=mes, anio=anio) + '?pdf=1')


# ==================== ADMIN · INFORME PENDIENTES CUESTIONARIO ====================
@app.route('/admin/cuestionario/pendientes')
@admin_required
def admin_cuestionario_pendientes():
    pendientes = _pendientes_por_cliente()
    total_clientes = len(pendientes)
    total_pendientes = sum(len(p) for _, p in pendientes)
    return render_template(
        'admin/cuestionario_pendientes.html',
        pendientes=pendientes,
        total_clientes=total_clientes,
        total_pendientes=total_pendientes,
    )


# ==================== MIS HORAS DEL MES (trabajador ve solo las suyas; admin puede ver todas) ====================

@app.route('/horas/mes/<int:mes>/<int:anio>')
@login_required
def horas_mes(mes, anio):
    """Vista de horas del mes: trabajador ve solo las suyas; admin ve todas (misma estructura que informe_horas_mensual)."""
    inicio_mes, fin_mes = _rango_mes(mes, anio)
    if session.get('rol') != 'ADMIN':
        tid = session.get('trabajador_id')
        if not tid:
            flash('No tienes un trabajador asociado', 'error')
            return redirect(url_for('horas_semana'))
        registros = RegistroHora.query.filter(
            RegistroHora.trabajador_id == tid,
            RegistroHora.fecha >= inicio_mes,
            RegistroHora.fecha < fin_mes
        ).order_by(RegistroHora.fecha, RegistroHora.cliente_id, RegistroHora.tarea_id).all()
    else:
        registros = RegistroHora.query.filter(
            RegistroHora.fecha >= inicio_mes,
            RegistroHora.fecha < fin_mes
        ).order_by(RegistroHora.trabajador_id, RegistroHora.cliente_id, RegistroHora.tarea_id).all()

    por_trabajador = {}
    for r in registros:
        tid = r.trabajador_id
        if tid not in por_trabajador:
            por_trabajador[tid] = {'nombre': r.trabajador.nombre, 'lineas': [], 'total': Decimal('0')}
        horas_dec = r.horas
        por_trabajador[tid]['total'] += horas_dec
        lineas = por_trabajador[tid]['lineas']
        found = False
        for lin in lineas:
            if (lin.get('cliente_id'), lin.get('tarea_id')) == (r.cliente_id, r.tarea_id):
                lin['horas'] += horas_dec
                if r.observaciones:
                    if 'observaciones' not in lin:
                        lin['observaciones'] = []
                    lin['observaciones'].append(f"{r.fecha.strftime('%d/%m')}: {r.observaciones}")
                found = True
                break
        if not found:
            obs_list = []
            if r.observaciones:
                obs_list.append(f"{r.fecha.strftime('%d/%m')}: {r.observaciones}")
            lineas.append({
                'cliente': r.cliente.nombre,
                'cliente_id': r.cliente_id,
                'tarea': r.tarea.nombre,
                'tarea_id': r.tarea_id,
                'horas': horas_dec,
                'observaciones': obs_list,
            })
    total_general = sum(d['total'] for d in por_trabajador.values())
    # Acumulado del año (enero hasta mes actual inclusive), sin coste
    tids = list(por_trabajador.keys()) if por_trabajador else []
    acumulado_por_trabajador = {tid: _horas_acumulado_anio(anio, mes, [tid]) for tid in tids}
    total_acumulado_anio = sum(acumulado_por_trabajador.values()) if acumulado_por_trabajador else Decimal(0)
    for tid in por_trabajador:
        por_trabajador[tid]['acumulado_anio'] = acumulado_por_trabajador.get(tid, Decimal(0))
    nombres_meses = ('', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre')
    return render_template(
        'informe_horas_mensual.html',
        por_trabajador=por_trabajador,
        total_general=total_general,
        total_acumulado_anio=total_acumulado_anio,
        mes=mes,
        año=anio,
        nombre_mes=nombres_meses[mes] if 1 <= mes <= 12 else str(mes),
        es_admin=session.get('rol') == 'ADMIN',
        desde_informe=False,
    )


# ==================== INFORME MENSUAL DE HORAS (TODOS LOS TRABAJADORES; SIN COSTE) ====================

@app.route('/informes/horas-mensual/<int:mes>/<int:anio>')
@login_required
def informe_horas_mensual(mes, anio):
    """Informe de horas del mes y acumulado del año. Todos pueden verlo; trabajadores solo sus datos. Sin coste."""
    inicio_mes, fin_mes = _rango_mes(mes, anio)
    if session.get('rol') != 'ADMIN':
        tid = session.get('trabajador_id')
        if not tid:
            flash('No tienes un trabajador asociado', 'error')
            return redirect(url_for('horas_semana'))
        registros = RegistroHora.query.filter(
            RegistroHora.trabajador_id == tid,
            RegistroHora.fecha >= inicio_mes,
            RegistroHora.fecha < fin_mes
        ).order_by(RegistroHora.cliente_id, RegistroHora.tarea_id).all()
    else:
        registros = RegistroHora.query.filter(
            RegistroHora.fecha >= inicio_mes,
            RegistroHora.fecha < fin_mes
        ).order_by(RegistroHora.trabajador_id, RegistroHora.cliente_id, RegistroHora.tarea_id).all()
    # Agrupar por trabajador -> (cliente, tarea) -> horas y observaciones
    por_trabajador = {}
    for r in registros:
        tid = r.trabajador_id
        if tid not in por_trabajador:
            por_trabajador[tid] = {'nombre': r.trabajador.nombre, 'lineas': [], 'total': Decimal('0')}
        horas_dec = r.horas
        por_trabajador[tid]['total'] += horas_dec
        lineas = por_trabajador[tid]['lineas']
        found = False
        for lin in lineas:
            if (lin.get('cliente_id'), lin.get('tarea_id')) == (r.cliente_id, r.tarea_id):
                lin['horas'] += horas_dec
                if r.observaciones:
                    if 'observaciones' not in lin:
                        lin['observaciones'] = []
                    lin['observaciones'].append(f"{r.fecha.strftime('%d/%m')}: {r.observaciones}")
                found = True
                break
        if not found:
            obs_list = []
            if r.observaciones:
                obs_list.append(f"{r.fecha.strftime('%d/%m')}: {r.observaciones}")
            lineas.append({
                'cliente': r.cliente.nombre,
                'cliente_id': r.cliente_id,
                'tarea': r.tarea.nombre,
                'tarea_id': r.tarea_id,
                'horas': horas_dec,
                'observaciones': obs_list,
            })
    total_general = sum(d['total'] for d in por_trabajador.values())
    tids = list(por_trabajador.keys()) if por_trabajador else []
    acumulado_por_trabajador = {tid: _horas_acumulado_anio(anio, mes, [tid]) for tid in tids}
    total_acumulado_anio = sum(acumulado_por_trabajador.values()) if acumulado_por_trabajador else Decimal(0)
    for tid in por_trabajador:
        por_trabajador[tid]['acumulado_anio'] = acumulado_por_trabajador.get(tid, Decimal(0))
    nombres_meses = ('', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre')
    return render_template(
        'informe_horas_mensual.html',
        por_trabajador=por_trabajador,
        total_general=total_general,
        total_acumulado_anio=total_acumulado_anio,
        mes=mes,
        año=anio,
        nombre_mes=nombres_meses[mes] if 1 <= mes <= 12 else str(mes),
        es_admin=session.get('rol') == 'ADMIN',
        desde_informe=True,
    )


@app.route('/informes/horas-mensual/<int:mes>/<int:anio>/excel')
@login_required
def informe_horas_mensual_excel(mes, anio):
    """Exporta el informe mensual de horas a Excel (sin coste). Todos pueden; trabajadores solo sus datos."""
    inicio_mes, fin_mes = _rango_mes(mes, anio)
    if session.get('rol') != 'ADMIN':
        tid = session.get('trabajador_id')
        if not tid:
            flash('No tienes un trabajador asociado', 'error')
            return redirect(url_for('horas_semana'))
        registros = RegistroHora.query.filter(
            RegistroHora.trabajador_id == tid,
            RegistroHora.fecha >= inicio_mes,
            RegistroHora.fecha < fin_mes
        ).order_by(RegistroHora.cliente_id, RegistroHora.tarea_id).all()
    else:
        registros = RegistroHora.query.filter(
            RegistroHora.fecha >= inicio_mes,
            RegistroHora.fecha < fin_mes
        ).order_by(RegistroHora.trabajador_id, RegistroHora.cliente_id, RegistroHora.tarea_id).all()
    por_trabajador = {}
    for r in registros:
        tid = r.trabajador_id
        if tid not in por_trabajador:
            por_trabajador[tid] = {'nombre': r.trabajador.nombre, 'lineas': [], 'total': Decimal('0')}
        horas_dec = r.horas
        por_trabajador[tid]['total'] += horas_dec
        lineas = por_trabajador[tid]['lineas']
        found = False
        for lin in lineas:
            if (lin.get('cliente_id'), lin.get('tarea_id')) == (r.cliente_id, r.tarea_id):
                lin['horas'] += horas_dec
                if r.observaciones:
                    if 'observaciones' not in lin:
                        lin['observaciones'] = []
                    lin['observaciones'].append(f"{r.fecha.strftime('%d/%m')}: {r.observaciones}")
                found = True
                break
        if not found:
            obs_list = []
            if r.observaciones:
                obs_list.append(f"{r.fecha.strftime('%d/%m')}: {r.observaciones}")
            lineas.append({
                'cliente': r.cliente.nombre,
                'cliente_id': r.cliente_id,
                'tarea': r.tarea.nombre,
                'tarea_id': r.tarea_id,
                'horas': horas_dec,
                'observaciones': obs_list,
            })
    tids = list(por_trabajador.keys())
    for tid in tids:
        por_trabajador[tid]['acumulado_anio'] = _horas_acumulado_anio(anio, mes, [tid])
    total_acumulado_anio = sum(por_trabajador[t]['acumulado_anio'] for t in por_trabajador)
    nombres_meses = ('', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre')
    wb = Workbook()
    ws = wb.active
    ws.title = f"Horas {mes}-{anio}"
    header_font = Font(bold=True)
    ws.cell(row=1, column=1, value=f"INFORME MENSUAL DE HORAS - {nombres_meses[mes] if 1 <= mes <= 12 else str(mes)} {anio} (sin coste)")
    ws.cell(row=1, column=1).font = header_font
    row = 3
    for tid, dat in por_trabajador.items():
        ws.cell(row=row, column=1, value="Trabajador")
        ws.cell(row=row, column=2, value=dat['nombre'])
        ws.cell(row=row, column=1).font = header_font
        row += 1
        ws.cell(row=row, column=1, value="Cliente")
        ws.cell(row=row, column=2, value="Tarea")
        ws.cell(row=row, column=3, value="Horas")
        ws.cell(row=row, column=4, value="Observaciones")
        for c in range(1, 5):
            ws.cell(row=row, column=c).font = header_font
        row += 1
        for lin in dat['lineas']:
            ws.cell(row=row, column=1, value=lin['cliente'])
            ws.cell(row=row, column=2, value=lin['tarea'])
            ws.cell(row=row, column=3, value=float(lin['horas']))
            obs_text = '; '.join(lin.get('observaciones', [])) if lin.get('observaciones') else ''
            ws.cell(row=row, column=4, value=obs_text)
            row += 1
        ws.cell(row=row, column=1, value="Horas del mes")
        ws.cell(row=row, column=3, value=float(dat['total'])).font = header_font
        row += 1
        ws.cell(row=row, column=1, value=f"Acumulado año {anio} (ene-{nombres_meses[mes] if 1 <= mes <= 12 else str(mes)})")
        ws.cell(row=row, column=3, value=float(dat['acumulado_anio'])).font = header_font
        row += 2
    total_general = sum(d['total'] for d in por_trabajador.values())
    ws.cell(row=row, column=1, value="TOTAL HORAS DEL MES")
    ws.cell(row=row, column=3, value=float(total_general)).font = header_font
    row += 1
    ws.cell(row=row, column=1, value=f"TOTAL ACUMULADO AÑO {anio}")
    ws.cell(row=row, column=3, value=float(total_acumulado_anio)).font = header_font
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"informe_horas_mensual_{mes}_{anio}.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def init_db():
    """Inicializa la base de datos y crea tablas si no existen."""
    with app.app_context():
        db.create_all()
        seed_catalogo()
        _ensure_cuestionarios_normativos()
        
        # Crear usuario administrador por defecto si no existe
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(nombre='Administrador', username='admin', rol='ADMIN')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Usuario administrador creado: admin / admin")


# En Vercel (serverless), el scheduler en segundo plano no funciona.
# Para tareas programadas en producción, usa Vercel Cron Jobs.
# Ver: https://vercel.com/docs/cron-jobs

if __name__ == '__main__':
    init_db()
    
    # Scheduler: solo en desarrollo local
    try:
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
            sched = BackgroundScheduler(daemon=True)
            sched.add_job(
                func=_enviar_informe_pendientes_admin,
                trigger=CronTrigger(day=1, hour=8, minute=0),
                id="informe_pendientes_cuestionario",
                replace_existing=True,
            )
            sched.start()
    except Exception:
        pass
    
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # En producción (Vercel), inicializar la DB si DATABASE_URL está configurada
    if os.environ.get('DATABASE_URL'):
        try:
            init_db()
        except Exception as e:
            print(f"Warning: Could not initialize DB: {e}")

