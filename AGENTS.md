# Instrucciones para agentes — HuellasUY
## Misión
Facilitar avisos temporales sobre animales vistos en Uruguay. Resolver «vi un animal acá hace poco» con la menor complejidad razonable.
## Prioridades
Seguridad, privacidad, funcionamiento, simplicidad, accesibilidad, mantenibilidad y estética, en ese orden.
## Antes de modificar
Leer README, este archivo, arquitectura, decisiones y tests relevantes. Identificar el cambio mínimo, implementarlo, ejecutar `.venv-system/bin/python -m pytest -q` (o el entorno disponible), revisar seguridad y actualizar documentación.
## Restricciones
No introducir React, cuentas, fotos, chat, trackers, publicidad, dependencias grandes ni almacenamiento histórico sin pedido explícito. No cambiar las 24 horas sin decisión documentada. No confiar en el navegador para vencimientos. No guardar coordenadas originales, IPs ni tokens sin hash. No incluir secretos, bases de datos, `.env`, enlaces privados o alertas falsas en Git. No eliminar tests para hacerlos pasar.
## Arquitectura
Flask sirve frontend y JSON. SQLite es compartido en disco persistente. V1 no tiene autenticación; v2 opcional (`AUTH_ENABLED`) usa sesiones privadas en cookies HttpOnly/Secure/SameSite, correo verificado y Origin obligatorio en escrituras. No hay CORS público. Repositorio SQL en database.py. API en app.py. Interfaz en templates y static. La hora autoritativa es UTC del servidor. Los resultados públicos nunca incluyen hashes de eliminación. La limpieza elimina reportes y contadores de frecuencia vencidos.
## Verificación y entrega
Cada incremento debe permanecer ejecutable. Una tarea termina cuando pasan tests, funciona en móvil/teclado, no expone secretos ni rompe privacidad o expiración y tiene documentación actualizada. Informar los comandos y resultados realmente ejecutados, y cualquier límite de validación. No instalar herramientas críticas del sistema.
