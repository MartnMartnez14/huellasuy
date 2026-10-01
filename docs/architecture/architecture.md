# Arquitectura
Navegador → Flask (HTML, API, validación y reloj UTC) → SQLite persistente.
Leaflet → imágenes de OpenStreetMap. Google Maps solamente como enlace externo.

POST genera un token criptográfico y guarda su SHA-256. Solo la respuesta de creación entrega el token. GET filtra expires_at > now y nunca devuelve hashes. DELETE recibe el token en JSON. El enlace privado usa #token y se retira del historial al abrirlo.

Consultas cada 15 segundos mientras la página está visible; al volver se refresca. La interfaz usa hora del servidor para calcular vida restante y retira alertas vencidas cada 10 segundos, incluso sin conexión. La API sigue siendo la autoridad: ningún dato vencido se entrega.

Redondear a tres decimales antes de insertar. No guardar ubicación exacta. Repositorio pequeño en database.py; una migración futura a PostgreSQL requiere adaptar repositorio, transacciones y esquema, no el contrato frontend.
