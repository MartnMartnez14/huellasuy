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

No verificado: lectores de pantalla, dispositivos físicos, rendimiento con grandes volúmenes, despliegue HTTPS y topología de proxy. No se certifica WCAG completa. No se publicó en GitHub ni en hosting. La carpeta no contiene repositorio Git válido.

## Ajuste de apoyos y lista–mapa
Se ejecutaron nuevamente 19 tests de pytest (todos aprobados) y una prueba de Chrome contra una instancia local actualizada. `scripts/list_map_qa.cjs` simula reportes únicamente en el navegador, sin insertarlos en la base. Verificó selección correcta por teclado, conservación de popup después del refresco de 10 segundos, filtros, retiro de marcador/popup al eliminar una alerta en la siguiente consulta, anchos móvil/escritorio y los tres enlaces de apoyo. Opciones: PLAYWRIGHT_MODULE, CHROME_PATH y QA_URL para elegir runtime, navegador y servidor. Uruguay mantiene solo advertencia; validación territorial estricta pendiente para segunda versión.
