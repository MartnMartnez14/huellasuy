# Despliegue

## Alojamiento actual: PythonAnywhere
HuellasUY está disponible en https://buerianiloba98.pythonanywhere.com/, con Python 3.12, Flask y SQLite. El autor completó el despliegue y las pruebas manuales entre celular y PC. GitHub aloja el código; PythonAnywhere ejecuta la aplicación.

### Configurar una instalación propia
Los siguientes comandos se ejecutan en una **consola Bash del navegador de PythonAnywhere**, no en los campos de la pestaña Web:

```bash
git clone https://github.com/MartnMartnez14/huellasuy.git
cd ~/huellasuy
mkvirtualenv --python=/usr/bin/python3.12 huellasuy-env
pip install -r requirements.txt
python -m pytest -q
```

En **Web → Add a new web app**, elegir **Manual configuration** y **Python 3.12**. En los campos de esa página, reemplazar `TU_USUARIO` por el nombre de la cuenta:

| Campo | Valor |
| --- | --- |
| Source code | `/home/TU_USUARIO/huellasuy` |
| Working directory | `/home/TU_USUARIO/huellasuy` |
| Virtualenv | `/home/TU_USUARIO/.virtualenvs/huellasuy-env` |

Esas rutas se pegan en los campos del panel; no son comandos. Abrir el enlace **WSGI configuration file** y reemplazar su plantilla por:

```python
import os
import sys

project_path = "/home/TU_USUARIO/huellasuy"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ["DATABASE_PATH"] = project_path + "/instance/huellasuy.db"
os.environ["PUBLIC_ORIGIN"] = "https://TU_USUARIO.pythonanywhere.com"

from app import create_app
application = create_app()
```

Reemplazar ambos `TU_USUARIO` antes de guardar. La base se guarda en el espacio persistente de archivos de la cuenta, fuera de Git. La aplicación genera un secreto estable junto a la base si falta `SECRET_KEY`; preservar ese archivo y restringir acceso a la carpeta. No incluir secretos en archivos versionados ni compartirlos en capturas.

Guardar el WSGI, activar **Force HTTPS** y pulsar **Reload** desde Web. No iniciar `app.py` ni Gunicorn en una consola: PythonAnywhere ejecuta el objeto WSGI. Opcionalmente configurar `/static/` en **Static files** apuntando a `/home/TU_USUARIO/huellasuy/static`; nunca exponer `instance/` ni toda la carpeta del proyecto. Revisar `/health` y el formulario desde la URL HTTPS.

Para actualizar el código desde la consola, con el entorno activado:

```bash
workon huellasuy-env
cd ~/huellasuy
git pull --ff-only
pip install -r requirements.txt
python -m pytest -q
```

Después pulsar **Reload** en Web. Las actualizaciones del repositorio no se despliegan automáticamente. No borrar ni reemplazar la base persistente al actualizar.

### Plan gratuito y mantenimiento
Condiciones oficiales verificadas el 3 de octubre de 2026: Beginner cuesta US$0/mes, ofrece una web, un worker, HTTPS y 512 MB de almacenamiento. No incluye tareas programadas para cuentas gratuitas nuevas. Ver [planes](https://www.pythonanywhere.com/pricing/).

La web gratuita requiere renovación: revisar **Best before date** y pulsar **Run until 1 month from today** antes de la fecha indicada. Esto es independiente de **Reload**, que aplica cambios de configuración/código. Ver [cambios del plan gratuito](https://blog.pythonanywhere.com/221/).

Los 100 CPU-seconds diarios se aplican a consolas/tareas, no actualmente a la aplicación web; esto no significa capacidad ilimitada de tráfico. El único worker atiende solicitudes en cola y el plan tiene ancho de banda limitado. No se afirma una cifra máxima de usuarios ni se garantiza disponibilidad; si aumenta el uso hay que medir y evaluar infraestructura adecuada. La restricción de conexiones salientes del servidor no se aplica a las consultas de Leaflet/tiles realizadas por el navegador visitante.

SQLite está disponible, pero el proveedor no lo recomienda como base de producción por su comportamiento en el sistema de archivos. Para esta primera etapa se mantiene la arquitectura probada; no hay pruebas de carga ni garantía de rendimiento concurrente. Ver [bases de datos](https://help.pythonanywhere.com/pages/KindsOfDatabases) y [guía WSGI de Flask](https://help.pythonanywhere.com/pages/Flask/).

La expiración no necesita cron: la API excluye reportes vencidos y limpia al consultar/iniciar. Sin actividad pueden quedar filas vencidas hasta la siguiente limpieza, siempre inaccesibles por la API. La limpieza periódica opcional indicada abajo corresponde a alojamientos que permitan tareas programadas.

## Alternativa: otro servidor Linux
En Linux, con las dependencias instaladas:
```bash
export DATABASE_PATH=/ruta/volumen-persistente/huellasuy.db
export PUBLIC_ORIGIN=https://tu-dominio.example
export SECRET_KEY='reemplazar-por-un-secreto-aleatorio'
.venv/bin/gunicorn --workers 1 --threads 4 --bind 127.0.0.1:8000 'app:create_app()'
```
Usar TLS en un proxy o plataforma, y configurar el dominio público. No ejecutar `app.py` ni el servidor de desarrollo para producción. Una instancia y un volumen local: SQLite no es adecuado para varias máquinas escribiendo el mismo archivo. Mantener secreto estable y restringir permisos del volumen al usuario del servicio.

Programar cada cinco minutos (con rutas absolutas y las mismas variables):
```bash
.venv/bin/flask --app app:create_app cleanup
```
La API oculta vencidos incluso si falla el cron. Evitar backups duraderos de reportes temporales; rotar registros del proveedor y no registrar cuerpos ni query strings privados. SQLite puede conservar rastros de filas borradas en páginas libres: no representa una garantía de borrado forense.

El límite de frecuencia usa remote_addr. Detrás de un proxy sin configuración específica todos pueden compartir un límite. Ajustar el proxy confiable según topología antes de publicar; no confiar ciegamente en X-Forwarded-For. Comprobar desde dos dispositivos la publicación, eliminación y el ciclo de 24 horas. Supervisar /health, almacenamiento y errores; sin métricas con datos personales.

Leaflet se carga de un CDN. Si falla, quedan lista y campos de coordenadas. Los tiles estándar de OSM son un servicio de capacidad limitada, sin SLA; mantener atribución y Referer, respetar cache del navegador y no descargar mapas masivamente/offline. Para mayor tráfico elegir otro proveedor. [Política oficial](https://operations.osmfoundation.org/policies/tiles/), revisada 2026-10-01.

Google Maps se usa solo mediante enlaces. Un eventual cambio de proveedor visual requiere actualizar map.js, CSP, atribución y documentación; nunca incorporar una clave secreta en el frontend.
