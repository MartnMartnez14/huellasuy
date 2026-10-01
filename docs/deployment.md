# Despliegue
Estado: preparado para servidor Python; proveedor y URL pública pendientes. No se afirma que ningún plan gratuito incluya disco persistente. Antes de contratar, comprobar precios, suspensión por inactividad, Python, HTTPS, persistencia y backups del plan vigente.

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
