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
