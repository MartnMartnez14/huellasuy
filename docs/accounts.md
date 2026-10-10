# HuellasUY v2.0 — cuentas verificadas

Entrega acotada: cuentas, recuperación, emoji y administración. Las alertas conservan 24 horas y no incluyen fotos ni comentarios. La activación es explícita (`AUTH_ENABLED=1`) después de copia privada de SQLite y comprobación de correo. El estado del despliegue real se registra en verification.md; publicar código en GitHub no activa PythonAnywhere.

## Funciones disponibles

Registro con usuario (3–30 caracteres, letras, números y `_`), correo privado y contraseña de 12–128 caracteres. Emoji aleatorio persistente. Verificación de correo (24 horas), recuperación (30 minutos), sesión de siete días y cierre de sesión. Contraseñas con scrypt de Werkzeug; tokens y sesiones guardados únicamente como SHA-256. Recuperar contraseña invalida todas las sesiones.

Al habilitar cuentas, el servidor protege mapa, lista y detalles: `GET /api/reports` y publicación devuelven 401 sin sesión verificada. La portada solo muestra una ilustración desenfocada y el formulario de acceso, sin cargar datos reales ni Leaflet. Los enlaces compartidos requieren acceso. Los enlaces privados anteriores conservan la capacidad de borrar con token; para usar su interfaz se requiere entrar y el fragmento permanece hasta que la interfaz de gestión lo captura.

Los nuevos reportes registran `author_id` internamente. La migración añade esa columna a reportes existentes sin atribuirlos a otra persona ni alterar sus vencimientos. El esquema nuevo de cuentas se crea de forma idempotente. El autor autenticado puede borrar su alerta sin guardar un enlace; el administrador puede retirarla. Los enlaces privados continúan siendo capacidades de eliminación.

`ADMIN_EMAIL` se configura fuera de Git. Solo el usuario con ese correo verificado obtiene el borde dorado, etiqueta Administrador y acceso `/admin`. Puede revisar las últimas 100 alertas y cuentas, retirar alertas, suspender y rehabilitar cuentas. No puede suspenderse. Suspender revoca sesiones y enlaces pendientes; no equivale a retirar todas sus alertas.

## Configuración en PythonAnywhere

El remitente y el envío real desde PythonAnywhere fueron confirmados por el autor el 10 de octubre de 2026. El archivo de credenciales está en `~/.config/huellasuy/brevo.json`, fuera del repositorio, con permisos 600; directorio 700. Sus campos son `api_key`, `sender_email` y `sender_name`. No copiar su contenido a Issues, capturas o Git.

Antes de `create_app()` en WSGI:

```python
os.environ['AUTH_ENABLED'] = '1'
os.environ['ADMIN_EMAIL'] = 'TU_CORREO_VERIFICADO'
os.environ['SESSION_COOKIE_SECURE'] = '1'
os.environ['PUBLIC_ORIGIN'] = 'https://TU_USUARIO.pythonanywhere.com'
```

Usar la ruta SQLite persistente actual y el mismo secreto estable; no reemplazarlos. `BREVO_CONFIG_PATH` permite cambiar la ruta privada. Localmente usar `SESSION_COOKIE_SECURE=0` solo para HTTP de desarrollo. La entrega se puede activar tras las pruebas descritas abajo; fotos, comentarios, perfiles de contacto y duraciones opcionales se posponen a otra entrega y no son requisitos de esta versión.

Brevo envía por HTTPS un correo de texto simple, sin imágenes ni enlaces HTML de seguimiento. No se usan opciones de API no documentadas para prometer desactivar seguimiento. El proveedor recibe el destinatario y contenido del mensaje; revisar su configuración y retención de registros/previsualizaciones. [Configuración oficial de anonimización](https://help.brevo.com/hc/es/articles/11643306229906--Puedo-hacer-que-el-seguimiento-de-aperturas-y-clics-de-mis-emails-sea-an%C3%B3nimo). Los enlaces de cuenta llevan el token en el fragmento, no en parámetros de solicitud. Se retira del historial al abrir la página; un botón explícito consume el enlace. No se verifica automáticamente al abrirlo. Falta comprobar el correo de verificación real de esta implementación, incluidos enlaces y comportamiento del proveedor.

## API y límites

`GET /api/auth/me`; `POST /api/auth/register`, `/login`, `/logout`, `/verify`, `/forgot`, `/reset`, `/resend`. Operaciones administrativas: `POST /api/auth/admin/remove` con `report_id`; `/suspend` con `user_id` y `disabled` booleano. Cuerpo JSON obligatorio y Origin exacto del mismo sitio en todas las escrituras de cuentas; no permitir CORS. Cookie HttpOnly, SameSite=Lax, Secure en HTTPS. No guardar credenciales en localStorage.

Hasta 20 intentos de autenticación por hora por HMAC de IP, persistentes en SQLite. Envío limitado por este control y por el cupo de Brevo; redes compartidas pueden alcanzar el límite. Respuestas de recuperación y reenvío no confirman si existe el correo. Registro/login tampoco muestran correos, hashes ni tokens. No anunciar verificación o recuperación completada hasta confirmar el token en el servidor.

No añadir cuentas con verificación ficticia en producción. Las pruebas usan un emisor de correo simulado y una base temporal. Cuentas pendientes siguen almacenadas para permitir reenviar; no hay borrado automático de cuentas ni interfaz para cerrar la cuenta todavía. No se ofrece verificación de identidad real ni garantía de veracidad.

## Siguientes incrementos acordados

Una foto opcional para alertas de 24 horas; alertas de 48 horas o siete días sin foto. Comentarios de texto temporales, borrado propio y denuncias. Contactos Facebook/Instagram/WhatsApp voluntarios y no verificados. Borrado de fotos y comentarios junto a la alerta. Estos elementos todavía no están implementados ni desplegados.


## Cierre y despliegue de esta entrega

1. Mantener la base y `.secret` actuales; crear una copia privada de SQLite con su API de backup (no copiar archivos mientras se escriben). Guardar también el WSGI fuera de carpetas públicas. No subir esos archivos a Git.
2. En Bash de PythonAnywhere: `cd ~/huellasuy`, `git pull --ff-only`, `workon huellasuy-env`, `pip install -r requirements.txt`, `python -m pytest -q`. Si falla algún paso, no recargar.
3. En Web → WSGI, conservar rutas/import y añadir las variables indicadas arriba. Configurar el correo administrador exacto en ese archivo privado. Confirmar Force HTTPS y Reload.
4. Sin sesión, verificar portada ilustrativa y API de reportes bloqueada. Crear la cuenta del autor, recibir el correo real, copiar el enlace completo y confirmar. Entrar y comprobar borde dorado y `/admin`.
5. Crear una alerta identificada como prueba y eliminarla con el botón de autor. Desde otra sesión comprobar desaparición. Probar recuperación real: confirmar nueva contraseña e invalidación de la sesión anterior. No compartir los enlaces privados.
6. Si falla el registro/correo, mantener la cuenta pendiente y usar Reenviar verificación. Si falla la nueva versión, `AUTH_ENABLED=0` y Reload restituyen el comportamiento v1 conservando cuentas y avisos. La copia de respaldo sirve para recuperación manual; no restaurarla encima de nuevas publicaciones.
7. Registrar resultado manual antes de anunciar v2. Las comprobaciones locales no acreditan envío real de enlaces, tráfico ni capacidad de producción.

GitHub Pages no ejecuta Flask ni sustituye PythonAnywhere. La URL Pages comprobada el 10 de octubre devolvió 404; esta entrega conserva el README de GitHub como presentación y la URL PythonAnywhere como aplicación. No se publica una segunda aplicación estática con un mapa o datos ficticios.
