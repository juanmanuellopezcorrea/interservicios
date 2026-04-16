# Gestión de Servicios Profesionales

Aplicación web para la gestión de clientes, trabajadores, tareas e imputación de horas con generación de informes mensuales.

## Características

- **Gestión de Clientes**: Registro de clientes con cuota mensual fija
- **Gestión de Trabajadores**: Registro de trabajadores con coste por hora
- **Gestión de Tareas**: Definición de tareas indicando si están incluidas en contrato o son facturables
- **Registro de Horas**: Sistema de imputación de horas trabajadas con cálculos automáticos
- **Informes Mensuales**: Generación de informes en Excel con resumen económico y de horas
- **Sistema de Usuarios**: Dos roles (Administrador y Trabajador) con permisos diferenciados

## Requisitos del Sistema

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación

### 1. Instalar Python

Asegúrese de tener Python 3.8 o superior instalado. Puede verificar la versión ejecutando:

```bash
python --version
```

### 2. Crear entorno virtual (recomendado)

Es recomendable crear un entorno virtual para aislar las dependencias del proyecto:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

Instale las dependencias necesarias usando pip:

```bash
pip install -r requirements.txt
```

## Configuración

### Base de datos

La aplicación utiliza SQLite como base de datos. La base de datos se creará automáticamente al ejecutar la aplicación por primera vez.

### Usuario Administrador por defecto

La aplicación crea automáticamente un usuario administrador con las siguientes credenciales:
- **Usuario**: admin
- **Contraseña**: admin

**IMPORTANTE**: Cambie la contraseña del administrador después del primer acceso por razones de seguridad.

## Ejecución

### Modo Desarrollo

Para ejecutar la aplicación en modo desarrollo:

```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

### Modo Producción (Servidor)

Para ejecutar la aplicación en un servidor de producción, se recomienda usar un servidor WSGI como Gunicorn.

#### Instalación de Gunicorn

```bash
pip install gunicorn
```

#### Ejecutar con Gunicorn

**Windows:**
Gunicorn no está disponible en Windows. Puede usar Waitress como alternativa:

```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

**Linux/Mac:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Acceso desde otros equipos

Para que la aplicación sea accesible desde otros ordenadores en la red:

1. Asegúrese de que el servidor esté ejecutándose en `0.0.0.0` (ya configurado en el código)
2. Los usuarios pueden acceder usando: `http://[IP_DEL_SERVIDOR]:5000`

**Nota**: Reemplace `[IP_DEL_SERVIDOR]` con la dirección IP del servidor donde se ejecuta la aplicación.

## Uso

### Roles de Usuario

#### Administrador

El administrador tiene acceso completo a todas las funcionalidades:
- Gestión de clientes, trabajadores y tareas
- Ver todas las imputaciones de horas
- Generar y descargar informes mensuales
- Ver todos los datos económicos

#### Trabajador

Los trabajadores tienen acceso limitado:
- Solo pueden ver y gestionar sus propias imputaciones de horas
- No pueden ver datos económicos ni datos de otros trabajadores
- No pueden acceder a la gestión de clientes, trabajadores o tareas

### Flujo de Trabajo

1. **Configuración inicial (Administrador)**:
   - Crear clientes con sus cuotas mensuales
   - Crear trabajadores con sus costes por hora
   - Crear tareas indicando si están incluidas en contrato
   - Para tareas fuera de contrato, definir el precio por hora

2. **Registro de Horas (Trabajadores/Administrador)**:
   - Los trabajadores registran sus horas trabajadas
   - El sistema calcula automáticamente:
     - Coste de las horas (horas × coste hora del trabajador)
     - Importe a facturar si la tarea está fuera de contrato

3. **Generación de Informes (Administrador)**:
   - Seleccionar cliente, mes y año
   - El sistema genera un informe Excel con:
     - Tareas fuera de contrato con detalle
     - Resumen económico (cuota, ingresos extras, coste, resultado)
     - Resumen de horas por trabajador y por tarea

## Estructura del Proyecto

```
.
├── app.py                 # Aplicación Flask principal
├── models.py              # Modelos de base de datos
├── requirements.txt       # Dependencias del proyecto
├── README.md             # Este archivo
├── servicios_profesionales.db  # Base de datos (se crea automáticamente)
├── templates/            # Plantillas HTML
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── clientes.html
│   ├── cliente_form.html
│   ├── trabajadores.html
│   ├── trabajador_form.html
│   ├── tareas.html
│   ├── tarea_form.html
│   ├── horas.html
│   ├── hora_form.html
│   └── informe.html
├── static/               # Archivos estáticos
│   ├── css/
│   │   └── style.css
│   └── js/
└── temp/                 # Archivos temporales (informes Excel)
```

## Cálculos Realizados

### Coste de Horas
```
Coste Total = Horas Trabajadas × Coste por Hora del Trabajador
```

### Importe a Facturar (tareas fuera de contrato)
```
Importe Facturar = Horas Trabajadas × Precio por Hora de la Tarea
```

### Resultado Económico (Informe Mensual)
```
Resultado = Cuota Mensual + Ingresos por Extras - Coste Total de Horas
```

## Seguridad

- Las contraseñas se almacenan usando hash (Werkzeug)
- Cada usuario solo puede ver y editar sus propios datos (trabajadores)
- Los administradores tienen control total sobre todos los datos
- Cambie la contraseña del administrador por defecto después de la instalación
- Para producción, considere cambiar la clave secreta en `app.py`

## Soporte

Para problemas o preguntas, consulte la documentación o contacte al administrador del sistema.

## Licencia

Este software es de uso interno de la empresa.
