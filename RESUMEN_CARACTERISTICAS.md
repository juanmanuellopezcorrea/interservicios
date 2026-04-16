# Gestión de Servicios Profesionales – Resumen de características

## Qué es
Aplicación web (Flask + SQLite) para gestionar **trabajadores**, **clientes**, **tareas** y **horas trabajadas**, con informes de horas y de facturación. Se usa en el navegador en **http://127.0.0.1:5000**.

---

## Usuarios y seguridad
- **Login** con email y contraseña (o usuario alternativo para cuentas antiguas).
- **Cambio de contraseña** desde el menú (mínimo 6 caracteres).
- **Tres roles:** Administrador, Trabajador facturación, Trabajador (acceso limitado).
- Contraseña inicial del admin: **admin** / **admin** (solo para primera configuración).
- Alta de trabajadores: la app **genera la contraseña** y el admin se la comunica al usuario.

---

## Gestión de datos
- **Trabajadores:** nombre, email (usuario de login), rol, coste por hora (€), activo/inactivo. Solo el administrador los crea y edita.
- **Clientes:** nombre, modalidad de cuota (Sin cuota, Básico, Plus, Premium), tareas incluidas en contrato, datos opcionales (epígrafes IAE, etc.). Alta, edición, listado e **importación desde Excel**.
- **Tareas:** nombre, tipo (Cliente/Interna), si están en cuota o son facturables, límites y tarifas. Alta, edición, listado e **importación desde Excel**.

---

## Registro de horas
- **Registro semanal:** elegir semana (lunes), tarea, cliente y horas por día. Admin puede registrar por cualquier trabajador.
- **Mis horas del mes:** vista del mes actual con **acumulado del año (YTD)**.
- Posibilidad de **borrar horas** (eliminar registro o poner 0 y guardar).

---

## Informes
- **Informe de horas (mensual):** por mes/año, por trabajador, **sin coste**; incluye **acumulado del año**. Exportación a Excel. Acceso para todos los roles (cada uno ve lo que le corresponde).
- **Informe final de horas:** por cliente, columnas por trabajador (horas) y columna de coste. Exportación a Excel.
- **Informe de facturación:** solo **Administrador** y **Trabajador facturación**. Servicios facturables por cliente; **sin cuota mensual**; facturación fuera de cuota = **horas × coste/hora del trabajador**.
- **Informes de administrador:** costes, horas, facturación y otros; solo para el rol Admin.

---

## Permisos por rol (resumen)

| Rol | Horas | Clientes/Tareas | Informe facturación | Trabajadores / Informes admin |
|-----|-------|-----------------|---------------------|-------------------------------|
| **Trabajador** | Sí (solo las suyas) | Sí (alta/edición) | No | No |
| **Trabajador facturación** | Sí | Sí | Sí | No |
| **Administrador** | Sí (todas) | Sí | Sí | Sí |

---

## Tecnología y uso
- **Base de datos:** SQLite (`servicios_profesionales.db` en la carpeta del proyecto).
- **Arranque:** doble clic en `iniciar_aplicacion.bat` o `python app.py`; mantener la ventana abierta.
- **Manual detallado:** en el proyecto está `MANUAL_APP.md` con inicio, roles, menú, pasos de cada pantalla, solución de problemas y ejemplos de Excel para importar.
