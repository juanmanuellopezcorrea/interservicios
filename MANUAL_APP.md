# Manual de uso – Gestión de Servicios Profesionales

## Índice

1. [Inicio de la aplicación](#1-inicio-de-la-aplicación)
2. [Inicio de sesión](#2-inicio-de-sesión)
3. [Roles y permisos](#3-roles-y-permisos)
4. [Menú principal](#4-menú-principal-según-tu-rol)
5. [Trabajadores](#5-trabajadores-solo-administrador)
6. [Clientes](#6-clientes)
7. [Tareas](#7-tareas)
8. [Registro de horas](#8-registro-de-horas)
9. [Informes de horas](#9-informes-de-horas-todos-los-roles-sin-coste)
10. [Control Horario (fichaje)](#10-control-horario-fichaje)
11. [Informe de facturación](#11-informe-de-facturación-admin-y-trabajador-facturación)
12. [Informes (admin)](#12-informes-solo-administrador)
13. [Resumen rápido por rol](#13-resumen-rápido-por-rol)
14. [Solución de problemas](#14-solución-de-problemas)
15. [Ejemplos de formato Excel](#15-ejemplos-de-formato-excel-para-importar)
16. [Instalación en servidor](#16-instalación-en-servidor)
17. [Onboarding y compliance (clientes)](#17-onboarding-y-compliance-clientes)

---

## 1. Inicio de la aplicación

### Arrancar el servidor
- **Opción A:** Doble clic en el archivo `iniciar_aplicacion.bat` (en la carpeta del proyecto).
- **Opción B:** En una terminal:
  1. `cd "ruta\PROYECTO CURSOR"`
  2. Opcional: `.\venv\Scripts\Activate.ps1`
  3. `python app.py`

Mantén abierta la ventana mientras uses la aplicación.

### Acceder desde el navegador
- Abre el navegador y escribe: **http://127.0.0.1:5000**

---

## 2. Inicio de sesión

### Pantalla de entrada
- **Usuario (tu email):** El email que te ha asignado el administrador.
- **Contraseña:** La que te comunicaron al darte de alta (o la que hayas puesto si ya la cambiaste).
- Deja vacío el campo "Usuario alternativo" salvo que uses una cuenta antigua por nombre de usuario.

### Cuenta administrador por defecto
- Usuario: **admin** (en el campo "Usuario alternativo", dejando vacío el email).
- Contraseña: **admin**
- Solo para la primera configuración; cámbiala después.

### Cambiar contraseña
- Una vez dentro: menú **Cambiar contraseña**.
- Indica contraseña actual, nueva y confirmación (mínimo 6 caracteres).

---

## 3. Roles y permisos

| Rol | Registrar horas | Mis horas / Informe horas | Clientes | Tareas | Informe facturación | Trabajadores | Informes (admin) |
|-----|-----------------|---------------------------|----------|--------|---------------------|--------------|-------------------|
| **Trabajador** | Sí | Sí (solo las suyas) | Sí (alta/edición) | Sí (alta/edición) | No | No | No |
| **Trabajador facturación** | Sí | Sí | Sí | Sí | Sí | No | No |
| **Administrador** | Sí | Sí (todas) | Sí | Sí | Sí | Sí | Sí |

- **Sin coste:** En horas e informes de horas nunca se muestran importes ni costes.
- **Informe facturación:** Solo roles Administrador y Trabajador facturación.

---

## 4. Menú principal (según tu rol)

- **Registrar horas** – Registro semanal de horas.
- **Registro rápido** – Añadir horas en pocos clics y temporizador de tarea (ver sección 8).
- **Mis horas del mes** – Tus horas del mes actual con acumulado del año.
- **Informe horas** – Informe mensual de horas con selector de mes/año y acumulado del año.
- **Clientes** – Listado, alta, edición e importación.
- **Tareas** – Listado, alta, edición e importación.
- **Control Horario** – Fichaje de entrada/salida e informes de control horario (ver sección 10).
- **Fichar Entrada / Fichar Salida** – Botón en la barra (si tienes trabajador asociado); alterna entre registrar entrada o salida y muestra el tiempo en curso.
- **Informe facturación** – (Solo si tienes permiso) Servicios facturables por cliente.
- **Trabajadores** – (Solo admin) Alta, edición y listado de trabajadores.
- **Informes** – (Solo admin) Acceso a todos los informes (costes, horas, facturación, etc.).
- **Alertas compliance** – (Solo admin) Panel de alertas y revisiones normativas de referencia (ver [sección 17](#17-onboarding-y-compliance-clientes)).
- **Cambiar contraseña** – Cambio de contraseña.
- **Salir** – Cerrar sesión (al salir, cualquier fichaje abierto se cierra automáticamente).

---

## 5. Trabajadores (solo administrador)

### Dar de alta un trabajador
1. **Trabajadores** → **Nuevo Trabajador** (o botón equivalente).
2. Rellena:
   - **Nombre**
   - **Email** (será el usuario para entrar).
   - **Rol:** Trabajador, Trabajador facturación o Administrador.
   - **Coste por hora** (€).
3. Guardar. La aplicación genera una **contraseña automática** y la muestra en pantalla; comunícasela al trabajador.

### Editar un trabajador
- **Trabajadores** → **Editar** en la fila del trabajador.
- Puedes cambiar nombre, email, rol, coste, activo y, si quieres, **Nueva contraseña** (para resetearla).

### Reseteo de contraseña (admin)
- **Trabajadores** → **Editar** el trabajador → rellena **Nueva contraseña** → Guardar. Indica la nueva contraseña al trabajador.

---

## 6. Clientes

### Alta manual
1. **Clientes** → **Nuevo Cliente**.
2. **Nombre** y **Modalidad de cuota** (Sin cuota, Básico, Plus, Premium).
3. Opcional: Epígrafes IAE, horas asesoría fiscal.
4. Marca las **Tareas incluidas en contrato** (las no marcadas se facturan aparte).
5. Guardar.

### Editar / eliminar
- **Editar:** Clientes → **Editar** en la fila.
- **Eliminar:** Clientes → **Eliminar** (solo administrador). Se borran también los registros de horas de ese cliente.

### Onboarding y compliance (resumen)
- **Onboarding compliance** – Asistente por pasos para dar de alta un cliente con datos ampliados y generar obligaciones legales de referencia y lista de documentos.
- **Compliance** – En cada fila de cliente, botón **Compliance** para revisar obligaciones, marcar ítems y adjuntar documentos.
- Guía detallada: [sección 17](#17-onboarding-y-compliance-clientes).

### Importar desde Excel
1. **Clientes** → **Importar desde Excel**.
2. Archivo **.xlsx**, primera hoja.
3. **Columnas:**
   - **cliente** (o **nombre**) – Obligatorio. Nombre del cliente.
   - **tareas** – Opcional. Nombres de tareas separados por **;** (ej.: `Soporte; Mantenimiento`).
4. Los nombres de tareas deben existir ya en la aplicación. Los clientes que ya existan por nombre se omiten.

---

## 7. Tareas

### Alta manual
1. **Tareas** → **Nueva Tarea**.
2. **Nombre**, tipo (Cliente/Interna), inclusión en cuotas (básico, plus, premium), si es siempre facturable, límites, tarifas, etc.
3. Las tareas **incluidas en cuota** no se facturan aparte; el resto se factura (importe = horas × coste/hora del trabajador).

### Editar / eliminar
- **Editar:** Tareas → **Editar** en la fila.
- **Eliminar:** Tareas → **Eliminar**. Solo admin puede eliminar clientes; tareas pueden eliminarlas quienes tengan acceso. Se borran registros de horas asociados.

### Importar desde Excel
1. **Tareas** → **Importar desde Excel**.
2. Archivo .xlsx. Se busca la hoja "Tabla Maestra Tareas" o la primera.
3. Columna de nombre de tarea (según cabeceras del sistema). Las tareas que ya existan por nombre se omiten.

---

## 8. Registro de horas

### Registro semanal (recomendado)
1. **Registrar horas**.
2. Elige **Semana** (fecha del lunes) si quieres otra semana.
3. Elige **Tarea** y **Cliente**. (Si eres admin, también **Trabajador**.)
4. Introduce las horas por día en formato **H:MM** (ej. 1:30 = 1h 30min). Usa los botones rápidos (5m, 10m, 1h, etc.) si los hay.
5. Opcional: observaciones por día.
6. **Guardar** (o el botón de guardar del día para guardar solo ese día).

### Registro único (una fecha)
1. En la lista de horas (**Registrar horas** → **Ver semana**), enlace **Registro único**.
2. Elige trabajador (si eres admin), cliente, tarea, fecha y horas.
3. Guardar.

### Ver y editar registros
- **Registrar horas** → **Ver semana**: listado de registros con **Editar** y **Eliminar**.
- Un trabajador solo puede editar/eliminar sus propios registros; el admin puede todos.

### Borrar horas
- **Opción A:** En el listado (Ver semana) → **Eliminar** en la fila → confirmar.
- **Opción B:** En la vista semanal, poner **0** en las horas de ese día y guardar; se elimina ese registro.

### Registro rápido y temporizador (web)
Menú **⚡ Registro rápido** (requiere trabajador asociado a la sesión).

- **Modo Rápido:** Elige cliente, tarea y fecha; registra tiempo con botones **15m, 30m, 45m, 1h, 1h30, 2h** o escribe horas decimales (ej. 1,5). Las horas se **suman** al mismo cliente/tarea/fecha si ya existía un registro ese día. Mínimo **5 minutos** por operación; máximo **12 h** por operación.
- **Cliente con autocompletado:** escribe al menos **2 letras** en el campo cliente; aparecen sugerencias con las horas imputadas a ese cliente **en el mes actual**.
- **Plantillas:** puedes **guardar como plantilla** el cliente/tarea/nota y horas por defecto; **usar plantilla** rellena el formulario; **editar** o **eliminar** en la lista (cada trabajador solo ve las suyas).
- **Estadísticas del día:** recuadro con horas totales de hoy y cliente con más horas hoy.
- **Historial:** tabla filtrable por **hoy / semana / mes** y por cliente (actualización manual o al cambiar filtro).
- **Temporizador:** Elige cliente y tarea, pulsa **Iniciar**; **Pausar / Reanudar**. **Finalizar y guardar** abre un cuadro con **tiempo exacto** y opciones de **redondeo** (exacto, 15 min, 30 min, 1 h). El navegador puede mostrar una **notificación** al guardar (si das permiso).
- **Notificación si superas 8 h en un día** (una vez al día, si el navegador permite notificaciones).
- En la barra superior aparece un resumen cuando hay un temporizador activo.
- **Últimos registros:** enlaces **Repetir** para rellenar cliente y tarea.
- **Modo Visual:** **arrastra** una tarjeta de **tarea** sobre la zona de un **cliente** y elige minutos (15m, 30m, 1h, 2h) para registrar sin pasar por el formulario principal.

*Nota:* El acceso por **administrador** permite elegir **trabajador** en el registro rápido y en las plantillas asociadas a ese trabajador.

#### Arranque y base de datos
Al ejecutar `python app.py` (o `iniciar_aplicacion.bat`) desde la carpeta del proyecto, Flask crea las tablas que falten en SQLite (incluida **`plantillas_tarea`** si aún no existe).

#### Guía rápida de pruebas
1. Abre el navegador: **http://127.0.0.1:5000** o **http://localhost:5000**
2. **Inicia sesión** con el **email** y contraseña de tu trabajador (los que te dio el administrador), o con la cuenta **admin** en “Usuario alternativo” si aplica. *(Los ejemplos tipo `trabajador`/`trab123` solo sirven si existen en tu base de datos.)*
3. Menú → **⚡ Registro rápido**

**A) Autocompletado:** en “Cliente”, escribe al menos **2 letras** (ej. `abc`); deben aparecer sugerencias con horas del mes.

**B) Guardar plantilla:** elige cliente y tarea, opcionalmente horas/nota; rellena **nombre** en “Guardar como plantilla” y pulsa **💾 Guardar plantilla**.

**C) Usar plantilla:** en **Usar plantilla**, elige una y pulsa **Aplicar**; revisa los campos y registra con un botón de tiempo o **Guardar cantidad**.

**Manual en Word:** abre `MANUAL_APP.md` con Word (Archivo → Abrir) o copia el contenido desde el Bloc de notas y pégalo en un documento nuevo.

**Filtro de clientes:** el modelo **no** incluye `Cliente.activo`; el buscador filtra solo por **nombre**. Añadir “activo/inactivo” sería un cambio opcional en modelo y pantallas.

**Qué está implementado en registro rápido:** botones de tiempo, temporizador con pausa y redondeo, vista visual, plantillas, autocompletado, estadísticas del día, historial filtrable, notificaciones del navegador (si das permiso), arrastrar tarea a cliente en modo Visual, diseño adaptable a pantallas pequeñas.

**Opcional (no implementado):** sugerencias por patrones de uso, asistente por voz, widget de escritorio del sistema operativo.

**Checklist de pruebas:** login → registro rápido guarda horas → botones 15m–2h → autocompletado cliente → temporizador inicio/cuenta/pausa/fin → crear/usar plantilla → pestaña Visual (tarjetas y arrastre si aplica) → historial → **Repetir** en últimos registros → probar en móvil o ventana estrecha.

---

## 9. Informes de horas (todos los roles, sin coste)

### Mis horas del mes
- **Mis horas del mes**: horas del mes actual, desglose por cliente y tarea, y **acumulado del año** hasta ese mes.

### Informe horas
- **Informe horas**: mismo tipo de información con **selector de mes y año**.
- Muestra para cada trabajador (o solo el tuyo si no eres admin):
  - Horas del mes seleccionado.
  - **Acumulado del año** (desde enero hasta ese mes).
- Botón **Descargar Excel** (mismo contenido, sin coste).

---

## 10. Control Horario (fichaje)

El **Control Horario** permite registrar entrada y salida (fichaje) y generar informes en Excel con el tiempo trabajado por día, pausas y estado (Aprobado/Pendiente).

### Quién puede usar el fichaje
- Solo usuarios con **trabajador asociado** (entras con email de trabajador, o usuario con trabajador vinculado). Quien entra solo como usuario admin sin trabajador no puede fichar, pero sí ver la pantalla de Control Horario si es admin.

### Botón Fichar (barra superior)
- **Fichar Entrada**: al hacer clic se registra la hora de entrada y el botón pasa a **Fichar Salida** con un contador en vivo (ej. ⏱️ 02h 35m).
- **Fichar Salida**: cierra el fichaje actual y guarda la hora de salida y las horas trabajadas.
- Puedes hacer **varios fichajes al día** (mañana, tarde, etc.).
- Si cierras sesión con un fichaje abierto, se registra la salida automáticamente.

### Pestaña «Control Horario»
Según tu rol verás una u otra vista:

| Rol | Qué ves |
|-----|---------|
| **Trabajador** | Tu estado actual, fichajes de hoy, tus estadísticas (horas semana, mes y año), límite anual 1822 h y descarga de tu informe personal. |
| **Trabajador facturación** | Tu estado, tabla de todos los trabajadores con **horas de la semana** (no mes ni año), descarga de informe eligiendo trabajador y fechas. |
| **Administrador** | Tu estado, **alertas** si alguien supera 1822 h anuales o está cerca, tabla completa (semana, mes, año, % anual), **modificar estado** de fichajes y descarga de informes. |

### Alertas (solo administrador)
- **Límite anual:** 1822 horas por trabajador.
- **Alerta crítica (🔴):** el trabajador supera 1822 h en el año.
- **Alerta preventiva (🟡):** entre 90 % y 100 % del límite (1639,8–1822 h).
- Si hay alertas, al iniciar sesión como admin puedes ser redirigido a Control Horario y ver un aviso.

### Descargar informe Excel
- En Control Horario, elige **Desde** y **Hasta** y (si tienes permiso) el **Trabajador**. Pulsa **Generar informe Excel**.
- El archivo incluye: Día, Horario (entrada–salida), Horas totales, Total horas trabajadas, Total horas pausadas, Ubicación, **Estado** (Aprobado/Pendiente).
- Las **pausas** se calculan como el tiempo entre la salida de un fichaje y la entrada del siguiente del mismo día.

### Modificar la columna Estado (solo administrador)
- El informe Excel usa el **estado guardado** de cada día (no solo la fecha).
- En la sección **«Modificar estado en informes»** (solo admin) aparece una tabla con los últimos fichajes cerrados.
- En cada fila puedes elegir **Aprobado** o **Pendiente** y pulsar **Guardar**. El próximo informe Excel mostrará ese valor para ese día.

---

## 11. Informe de facturación (Admin y Trabajador facturación)

- **Informe facturación**: servicios facturables (fuera de cuota) por cliente y mes.
- Filtro por cliente y descarga Excel.
- Los importes se calculan como **horas × coste/hora** del trabajador (sin cuota mensual fija en el sistema).

---

## 12. Informes (solo administrador)

Desde **Informes** el admin puede acceder a:

- **Informe de horas realizadas en el mes** – Horas por trabajador, cliente y tarea (con Excel).
- **Informe de costes internos** – Horas por trabajador y coste por cliente (con Excel).
- **Informe final de horas** – Tabla: Cliente, columnas de horas por trabajador, columna Coste (con Excel).
- **Informe de facturación** – Enlace al informe de facturación.
- **Informe mensual por cliente (legacy)** – Generación de Excel por un solo cliente.

En todos los informes se elige **mes** y **año** en la parte superior.

---

## 13. Resumen rápido por rol

### Si eres Trabajador (acceso limitado)
- Entras con tu **email** y contraseña.
- Puedes: **Registrar horas**, ver **Mis horas del mes** e **Informe horas** (solo tus datos, sin coste), **Control Horario** (fichar y ver tus estadísticas e informe propio), y dar de alta/editar **Clientes** y **Tareas**.
- No ves Informe facturación ni gestión de trabajadores.

### Si eres Trabajador facturación
- Todo lo anterior y además: **Informe facturación** (ver y descargar) y en Control Horario ves **horas semanales de todos** los trabajadores y puedes descargar informes de cualquiera.

### Si eres Administrador
- Acceso completo: **Trabajadores**, **Informes**, **Alertas compliance**, **Control Horario** (alertas 1822 h, modificar estado de fichajes, informes de todos), eliminación de clientes y toda la configuración.

---

## 14. Solución de problemas

- **No arranca la aplicación:** Ejecuta `iniciar_aplicacion.bat` o `python app.py` desde la carpeta del proyecto y no cierres la ventana.
- **"Usuario o contraseña incorrectos":** Usa el **email** en "Usuario (tu email)" y la contraseña que te dieron. Si usas la cuenta admin antigua, deja el email vacío y pon **admin** en "Usuario alternativo" y **admin** en contraseña.
- **No puedo entrar como trabajador:** El administrador debe comprobar en Trabajadores que tengas **email**, que estés **Activo** y que te haya comunicado la contraseña (o resetearla en Editar trabajador).
- **Conexión rechazada (ERR_CONNECTION_REFUSED):** El servidor no está en marcha. En local: inicia la aplicación como en el apartado 1 (y usa **http://127.0.0.1:5000**). En un servidor: comprueba que Gunicorn o Waitress esté en ejecución y que el firewall permita el puerto (ej. 5000).
- **Error SQLite *no such column: clientes.activo* (u otra columna de cliente):** La base de datos es anterior al módulo de compliance. Ejecuta una vez `python migrate_compliance.py` desde la carpeta del proyecto (ver [17.1](#171-requisitos-previos-una-vez-por-instalación-o-tras-actualizar-el-proyecto)).

---

## 15. Ejemplos de formato Excel para importar

### Importar clientes

Archivo **.xlsx**, primera hoja. La **primera fila** debe ser la cabecera. Nombres de columna (no distinguen mayúsculas/minúsculas):

| Columna en el Excel | Obligatorio | Descripción |
|---------------------|-------------|-------------|
| **cliente** (o **nombre**, **nombre cliente**) | Sí | Nombre del cliente |
| **tareas** (o **tareas incluidas**) | No | Nombres de tareas separados por punto y coma (;) |

**Ejemplo de filas de datos:**

| cliente        | tareas                    |
|----------------|---------------------------|
| Empresa ABC SL | Soporte; Mantenimiento    |
| Consultora XYZ | Consultoría; Formación   |
| Cliente Test   | *(dejar vacío si no hay)* |

Las tareas deben existir previamente en la aplicación. Si un cliente ya existe por nombre, se omite.

---

### Importar tareas

Archivo **.xlsx**. Se usa la hoja **"Tabla Maestra Tareas"** si existe; si no, la primera hoja. La primera fila es la cabecera.

El sistema busca columnas cuyo nombre contenga:
- **nombre** y **tarea** → nombre de la tarea (obligatorio);
- **incluida** y **cuota** → si va incluida en cuota (opcional);
- **facturación** → precio/hora para facturación (opcional).

**Ejemplo orientativo de cabeceras:**

| Nombre de la tarea   | Incluida en cuota | Facturación |
|---------------------|-------------------|-------------|
| Soporte técnico     | Sí                |             |
| Consultoría        | No                | 45          |
| Formación          | No                | 60          |

Los nombres pueden variar; lo importante es que contengan las palabras indicadas. Las tareas que ya existan por nombre se omiten.

---

## 16. Instalación en servidor

Para usar la aplicación en un servidor (acceso por red o internet) en lugar de solo en tu PC, sigue una de las opciones según tu sistema.

### Requisitos
- Python 3.10 o superior.
- Dependencias: `Flask`, `Flask-SQLAlchemy`, `Werkzeug`, `openpyxl` (archivo `requirements.txt` en la carpeta del proyecto).

### 1. Subir el proyecto al servidor
- Copia toda la carpeta del proyecto (incluyendo `app.py`, `models.py`, `templates/`, `static/`, `requirements.txt`) al servidor.
- No es necesario subir la base de datos `servicios_profesionales.db` si quieres empezar de cero en el servidor; se creará al arrancar. Si ya la usas en local, puedes copiarla para llevar datos.

### 2. Configuración recomendada antes de desplegar
- **Clave secreta:** En `app.py` la aplicación usa `SECRET_KEY = 'clave-secreta-cambiar-en-produccion'`. En el servidor conviene cambiarla por una clave aleatoria y segura (por ejemplo generada con `python -c "import secrets; print(secrets.token_hex(32))"`) y guardarla en una variable de entorno si es posible.
- **Base de datos:** Por defecto se usa SQLite en el archivo `servicios_profesionales.db` dentro de la carpeta del proyecto. Asegúrate de que el usuario que ejecuta la aplicación tenga permisos de lectura y escritura en esa carpeta.

### 3. Opción A: Servidor Linux (con Gunicorn y Nginx)

**Instalar dependencias (ejemplo en Ubuntu/Debian):**
```bash
cd /ruta/del/proyecto
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

**Probar que la aplicación arranca:**
```bash
gunicorn -w 1 -b 0.0.0.0:5000 "app:app"
```
(Con `-w 1` se evitan problemas con SQLite en modo escritura desde varios procesos.)

**Servicio con systemd (para que arranque al iniciar el servidor):**  
Crea un archivo `/etc/systemd/system/gestion-servicios.service` (ajusta rutas y usuario):

```ini
[Unit]
Description=Gestion Servicios Profesionales
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/ruta/completa/al/proyecto
Environment="PATH=/ruta/completa/al/proyecto/venv/bin"
ExecStart=/ruta/completa/al/proyecto/venv/bin/gunicorn -w 1 -b 127.0.0.1:5000 "app:app"
Restart=always

[Install]
WantedBy=multi-user.target
```

Luego:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gestion-servicios
sudo systemctl start gestion-servicios
```

**Nginx como proxy inverso (opcional, para HTTPS y dominio):**  
En un sitio de Nginx puedes tener algo como:

```nginx
server {
    listen 80;
    server_name tudominio.com;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Después recarga Nginx. Para HTTPS puedes usar Certbot (Let's Encrypt).

### 4. Opción B: Servidor Windows

**Con Waitress (servidor WSGI para producción en Windows):**
```bash
cd C:\ruta\al\proyecto
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install waitress
```

**Arrancar:**
```bash
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

Puedes crear un script `.bat` o una tarea programada para que se ejecute al iniciar el servidor. Mantén la carpeta del proyecto con permisos de escritura para el usuario que ejecuta el proceso (para la base SQLite y posibles archivos generados).

### 5. Después de instalar
- Abre en el navegador la URL del servidor (ej. `http://IP-DEL-SERVIDOR:5000` o `https://tudominio.com` si configuraste Nginx).
- Inicia sesión con **admin** / **admin** (Usuario alternativo / contraseña) y cambia la contraseña en **Cambiar contraseña**.
- Crea trabajadores y configura clientes y tareas según necesites.
- El **Control Horario** y el resto de funciones (fichaje, informes Excel, etc.) funcionan igual que en local.

### 6. Copias de seguridad
- Haz copias periódicas del archivo `servicios_profesionales.db` (y de la carpeta del proyecto si aplica). En Linux puedes usar `cron`; en Windows, tareas programadas o copia manual.

---

## 17. Onboarding y compliance (clientes)

Esta parte de la aplicación ayuda a **recoger datos del cliente** de forma ordenada (onboarding) y a **llevar un seguimiento orientativo** de obligaciones legales de referencia en España (compliance). **No sustituye asesoramiento jurídico**; las obligaciones y plazos dependen del caso concreto y de la normativa vigente.

### 17.1. Requisitos previos (una vez por instalación o tras actualizar el proyecto)

1. **Base de datos con columnas nuevas**  
   Si la aplicación muestra errores del tipo *no such column: clientes.activo* (u otras columnas de cliente), desde la carpeta del proyecto ejecuta:
   ```text
   python migrate_compliance.py
   ```
   Esto añade a la tabla de clientes los campos necesarios para onboarding y compliance (sin borrar datos).

2. **Tablas nuevas**  
   Al arrancar la aplicación (`python app.py`), Flask crea automáticamente las tablas que falten (catálogo de obligaciones, obligaciones por cliente, documentos, informes, alertas).

3. **Catálogo de obligaciones**  
   Carga en la base el listado maestro de obligaciones de referencia (RGPD, PRL, registro horario, etc.):
   ```text
   python scripts\inicializar_catalogo_obligaciones.py
   ```
   Puedes ejecutarlo varias veces: **no duplica** códigos que ya existan.

4. **Dependencias**  
   En `requirements.txt` figura **APScheduler** (tareas programadas de revisión). Instálala con el resto: `pip install -r requirements.txt`.

5. **Archivos subidos**  
   Los documentos del onboarding se guardan en la carpeta `uploads_compliance` (se crea al subir el primer archivo). Inclúyela en tus **copias de seguridad** si usas esta función.

### 17.2. Onboarding de un cliente nuevo

**Quién:** cualquier usuario con acceso al menú **Clientes** (según tu política interna).

**Acceso:** **Clientes** → botón **Onboarding compliance**.

**Qué hace el asistente:** guía en **6 pasos** (barra de progreso):

| Paso | Contenido principal |
|------|---------------------|
| 1 | Datos básicos: nombre, razón social, CIF, tipo de sociedad, dirección fiscal, contactos |
| 2 | Actividad: CNAE, sector, empleados, previsión de plantilla, tipos de puesto, convenio |
| 3 | Económico: facturación, efectivo, datos bancarios, forma de pago, cuota mensual estimada con la gestoría |
| 4 | Local e instalaciones (si aplica): dirección del local, superficie, alimentos, climatización, etc. |
| 5 | Digital: web, redes, e-commerce, tratamiento de datos personales |
| 6 | Observaciones finales y **Finalizar onboarding** |

- **Siguiente:** guarda el paso actual y avanza.
- **Cancelar:** abandona el asistente y vuelve al listado de clientes (el borrador del cliente creado puede quedar en base; puedes editarlo o eliminarlo desde **Clientes** si no lo necesitas).

**Al finalizar (paso 6):** el sistema:

- Marca el cliente como onboarding completado.
- Genera la **lista de documentos** de onboarding (según tipo de entidad, empleados, local, etc.).
- **Evalúa el catálogo** y crea las **obligaciones aplicables** a ese cliente según reglas configuradas (empleados, local, datos personales, CNAE, etc.).
- Crea un **informe de compliance inicial** y genera el **HTML del correo** informativo para el cliente (contenido guardado en el informe).

**Redirección:** tras finalizar, se abre la pantalla **Compliance** de ese cliente.

### 17.3. Pantalla Compliance (por cliente)

**Acceso:** en **Clientes**, botón **Compliance** en la fila del cliente. También al terminar el onboarding.

**Parte superior**

- **Porcentaje global** y nivel de riesgo orientativo (se recalcula al actualizar obligaciones).
- **Editar cliente** – enlaza al formulario clásico de cliente (cuota, tareas incluidas, etc.).
- **Generar informe / email** – crea un informe tipo “manual” y vuelve a generar el HTML del email con las obligaciones pendientes/en curso que tengan marcado “incluir en email”.

**Envío real de correo:** por defecto **no** se envía correo externo. Para activarlo en el futuro hay que configurar en la aplicación el envío (por ejemplo Flask-Mail u otro proveedor) y la variable de configuración **`COMPLIANCE_MAIL_ENABLED`**. Hasta entonces, el HTML queda guardado en el informe para copiarlo o adjuntarlo manualmente.

**Documentación de onboarding**

- Tabla con documentos sugeridos (CIF, mandato SEPA, licencias si hay local, etc.).
- **Subir:** elige archivo y pulsa **Subir**; el estado pasa a “subido” (luego podrías validar internamente fuera de la app o ampliar el flujo).

**Detalle de obligaciones**

- Cada obligación muestra el **marco legal de referencia** y una lista de **ítems** (tareas o controles).
- Para cada ítem puedes marcar: **Pendiente**, **En proceso**, **Cumplido**.
- **Incluir en email** – si está marcado, ese bloque se tendrá en cuenta al generar el HTML del correo.
- **Guardar obligación** – guarda cambios y **recalcula** el porcentaje global del cliente.

### 17.4. Alertas de compliance (solo administrador)

**Acceso:** menú **Alertas compliance**.

**Qué verás:** alertas en estado pendiente (por ejemplo, revisión anual sugerida o avisos por fechas de vencimiento si están rellenadas en documentos u obligaciones).

**Acciones típicas**

- **En revisión** – deja constancia de que alguien está tratando el caso y abre la ficha **Compliance** del cliente.
- **Resolver** – cierra la alerta (puedes añadir notas en el campo de texto).
- **Ejecutar revisión manual** – lanza de inmediato las comprobaciones que, en horario programado, revisan clientes sin análisis reciente y posibles vencimientos próximos.

**Tareas programadas (opcional):** con el servidor en marcha, pueden ejecutarse trabajos automáticos (por ejemplo revisión diaria y revisión semanal de vencimientos). Si no quieres el planificador en un entorno concreto, puedes definir la variable de entorno **`DISABLE_COMPLIANCE_SCHEDULER=1`** antes de arrancar.

**Nota multi-proceso:** si en producción usas varios workers (varios procesos Gunicorn), cada uno tiene su propio identificador de arranque; en ese escenario conviene documentar internamente el uso del planificador o centralizar revisiones con la **revisión manual** desde el menú.

### 17.5. Clientes ya existentes (sin pasar por el onboarding)

- Puedes abrir **Compliance** en cualquier cliente: si aún **no** tiene obligaciones generadas, la lista puede estar vacía hasta que alguien complete datos en el cliente y exista lógica que vuelva a ejecutar el análisis, o hasta que uses procesos internos que añadan obligaciones manualmente en base de datos.  
- La forma **recomendada** para un alta completa sigue siendo **Onboarding compliance** para nuevos clientes, o completar los nuevos campos del cliente en **Editar** y valorar un desarrollo futuro de “recalcular obligaciones” si lo necesitáis.

### 17.6. Resumen rápido de flujo

1. Ejecutar **`migrate_compliance.py`** y **`scripts\inicializar_catalogo_obligaciones.py`** la primera vez (o tras migrar).
2. **Clientes** → **Onboarding compliance** → completar 6 pasos → **Finalizar**.
3. Revisar **Compliance**: documentos, ítems de obligaciones, **Generar informe / email** si procede.
4. **Admin** → **Alertas compliance** para seguimiento y **Ejecutar revisión manual** cuando convenga.

---

*Manual para la aplicación de Gestión de Servicios Profesionales. Incluye Control Horario, onboarding/compliance e instalación en servidor.*
