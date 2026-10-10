# Verificación del prototipo — 2026-10-01

Ejecutado con Python 3.12 del sistema en `.venv-system`:
```bash
.venv-system/bin/python -m pytest -q
python3 -m compileall -q app.py config.py database.py scripts/cleanup_expired.py
```
Resultado: 19 tests passed; compilación sin errores.

Ejecutado `scripts/browser_qa.cjs` con Playwright incluido en el runtime y Chrome instalado, contra Flask en puerto 5000 con base aislada `/tmp/huellas-browser.db`. Comprobaciones completadas:
- 360, 375, 390, 430, 768, 1024 y 1440 px sin desbordamiento horizontal, incluyendo modal.
- Dos contextos independientes: creación y eliminación visibles en la siguiente consulta periódica.
- Geolocalización concedida y rechazada; selección por toque.
- Formulario conservado al abortar una solicitud.
- Expiración simulada en una pestaña abierta con reloj del servidor.
- Cambio claro/oscuro.
- Cero errores JavaScript; 19 imágenes de mapa cargadas al finalizar.
- Capturas de escritorio y móvil generadas y revisadas visualmente.

Al finalizar esta revisión local inicial aún no se habían verificado dispositivos físicos ni despliegue público. El estado posterior se registra más abajo. Siguen pendientes lectores de pantalla, rendimiento con grandes volúmenes y auditoría de la topología del proxy. No se certifica WCAG completa.

## Ajuste de apoyos y lista–mapa
Se ejecutaron nuevamente 19 tests de pytest (todos aprobados) y una prueba de Chrome contra una instancia local actualizada. `scripts/list_map_qa.cjs` simula reportes únicamente en el navegador, sin insertarlos en la base. Verificó selección correcta por teclado, conservación de popup después del refresco de 10 segundos, filtros, retiro de marcador/popup al eliminar una alerta en la siguiente consulta, anchos móvil/escritorio y los tres enlaces de apoyo. Opciones: PLAYWRIGHT_MODULE, CHROME_PATH y QA_URL para elegir runtime, navegador y servidor. Uruguay mantiene solo advertencia; validación territorial estricta pendiente para segunda versión.


## Publicación y comprobaciones manuales — actualización 2026-10-03
Repositorio público: https://github.com/MartnMartnez14/huellasuy.
Aplicación alojada en PythonAnywhere: https://buerianiloba98.pythonanywhere.com/.

El 1 de octubre, el autor ejecutó `python -m pytest -q` dentro del entorno Python 3.12 de PythonAnywhere y compartió el resultado: **19 passed in 3.70s**. Configuró WSGI con `application = create_app()`, ruta absoluta para SQLite y origen HTTPS.

Según las pruebas y confirmaciones del autor:
- Publicación desde un dispositivo y visualización desde celular y PC.
- Navegación entre lista y mapa, formulario y ubicación.
- Eliminación mediante enlace privado desde celular y desaparición de la alerta en PC.
- El 3 de octubre confirmó que el reporte de prueba se eliminó automáticamente tras 24 horas.

Estas son comprobaciones manuales comunicadas por el autor, no una medición instrumentada del segundo exacto de vencimiento ni una nueva auditoría de infraestructura. No se guardan tokens privados ni coordenadas de pruebas en este registro. Las capturas proporcionadas se incluyen como documentación visual y se identifican como demostración.


## 10 de octubre de 2026 — base de cuentas v2 (local, desactivada)

- Emisor Brevo verificado y correo de prueba recibido desde PythonAnywhere: confirmación manual del autor. Todavía no se probó envío de enlaces de esta implementación contra el proveedor real.
- `.venv-system/bin/python -m pytest -q`: 26 pruebas aprobadas. Siete pruebas nuevas cubren registro/verificación, reutilización y vencimiento de tokens, cookies, sesión, recuperación y revocación, controles de origen, administrador y suspensión, fallos de correo, límites y persistencia de autor del reporte.
- Chrome/Playwright local con base aislada y correo simulado: registro y anchos 360, 390, 768 y 1440 sin desbordamiento ni errores JavaScript. Navegación básica mediante Tab; no equivale a auditoría completa de teclado o lector de pantalla.
- `git diff --check`: sin errores de formato. No se modificó ni activó la instancia pública. Documentos personales no rastreados se conservaron.
- Pendiente: flujo completo de enlaces reales, fotos/comentarios/contactos/duraciones, denuncias, cierre de cuenta, panel paginado y verificación integral antes del despliegue v2.

## Cierre v2.0 — 10 de octubre de 2026
Entrega limitada a cuentas y administración; no exige implementar fotos/comentarios para activarse. Pruebas adicionales de propiedad/borrado de alertas, transporte HTTPS de correo con credenciales simuladas y limpieza de token ante fallos. El envío de enlaces reales y activación pública siguen pendientes de ejecución en PythonAnywhere. GitHub Pages devolvió HTTP 404; no hay página estática que sincronizar en esa URL.

Validación de cierre local: 29 pruebas aprobadas en 7.93 s; Chrome con registro → verificación → acceso → recuperación → nuevo acceso, retirada administrativa y cierre que bloquea mapa. Cuatro anchos, sin errores JavaScript. Correo simulado; no se afirma comprobación de enlaces reales.

Corrección visual tras la prueba real de correo: las reglas display de componentes sobrescribían el atributo hidden en etiquetas y avisos. Se fija hidden de forma global; Verificar correo no muestra Nueva contraseña. El autor recibió el enlace real; confirmar su consumo y acceso sigue pendiente.

El autor confirmó en producción el 10 de octubre registro, recepción y confirmación del enlace, acceso con borde dorado, panel administrativo y publicación/eliminación de su alerta. Recuperación real e incógnito sin sesión siguen pendientes de confirmación. Se añade autor visible (usuario y emoji) en lista y popup del mapa, conservando correos privados.

Autor visible: `.venv-system/bin/python -m pytest -q`: 30 aprobadas en 8.30 s. Prueba de Chrome local con datos aislados confirmó el mismo usuario en lista y popup, tras filtro, sin errores JavaScript. La API ignora autor falsificado en el formulario, conserva identidad del creador frente a otro visitante y excluye correo/hashes.


## Confirmación manual en producción — 10 de octubre de 2026

El autor confirmó con capturas y pruebas en la instancia pública:
- Actualización en PythonAnywhere a `b7770d5` y ejecución de pytest: **30 passed in 17.46s**.
- Tras pulsar Reload en el panel Web, nombre de usuario y emoji visibles en lista y detalle del mapa. Un git pull por sí solo no recarga el proceso WSGI.
- Registro y acceso de una segunda cuenta con otro correo, recepción del correo de recuperación, cambio de contraseña y nuevo acceso satisfactorios.
- Publicación de una alerta desde esa cuenta con su identidad visible; borrado propio confirmado previamente con la cuenta principal.

Estas comprobaciones manuales comunicadas por el autor completan la prueba pendiente de recuperación real mediante Brevo. No prueban todos los proveedores de correo ni sustituyen una auditoría integral. No se incorporan las capturas de correo al repositorio porque contienen enlaces privados de recuperación. Sigue pendiente la confirmación manual de acceso sin sesión en incógnito; las restricciones de acceso ya están cubiertas por pruebas automatizadas. Fotos, comentarios y otras ampliaciones quedan fuera de esta entrega.
