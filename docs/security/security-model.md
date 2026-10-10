# Seguridad del prototipo
SQL parametrizado, validación de datos finitos y categorías cerradas, límites de texto/cuerpo, rechazo de etiquetas, Jinja autoescape y textContent en tarjetas. Token aleatorio de 32 bytes, hash SHA-256 y comparación constante. API sin cookies; JSON y comprobación de Origin/Sec-Fetch-Site impiden escrituras normales desde otro sitio. No son protección contra un atacante que llame directamente a la API.

Frecuencia: cinco publicaciones por hora por HMAC de IP, almacenado en SQLite y eliminado al limpiar al vencer la ventana. El límite persiste tras reinicio y puede afectar redes compartidas. Ver restricciones del proxy en deployment.md. No existe moderación humana automatizada; spam distribuido aún es posible. Administradores pueden retirar contenido mediante SQL controlado; panel de moderación fuera del MVP.

CSP, nosniff, Referrer-Policy y Permissions-Policy. HTTPS en producción. Tokens nunca en query strings ni logs de la aplicación. El fragmento solo se procesa en gestión. No analíticas ni cuentas. CDN, tiles y registros del alojamiento tienen políticas propias. Borrado lógico no garantiza borrado forense del disco o copias; limitar backups y retención.

## Cuentas en preparación
Las afirmaciones anteriores corresponden a v1 (`AUTH_ENABLED=0`). v2 opcional usa cookies de sesión opacas, hashes scrypt y Origin obligatorio en escrituras autenticadas; no basta con la comprobación opcional de Origin de v1. API de reportes protegida por servidor, portada ilustrativa sin datos. Correo y sesiones se describen en [cuentas](../accounts.md). Activar en público solo tras seguir el procedimiento de backup y pruebas de correo de la entrega acotada.
