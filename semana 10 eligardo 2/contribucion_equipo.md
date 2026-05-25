# 👥 Informe de Contribución del Equipo

## 📊 División del Trabajo
* **Integrante 1 (Arquitectura y Resiliencia):** Implementación del autómata de estados del `CircuitBreaker`, desarrollo de los casos de prueba automatizados con Pytest (`test_circuit_breaker.py` y `test_tc_x2_refresh_semiabierto.py`) y redacción del ADR Express.
* **Integrante 2 (Seguridad y Concurrencia):** Implementación del `TokenManager` con mitigación de errores Base64/JSON, integración del script orquestador `ClienteRobusto`, simulación del log de resiliencia y pruebas de control de Thundering Herd.

## ⚔️ Conflicto Técnico Resuelto
**Descripción del conflicto:** Durante el Reto 6 y Reto 8, debatimos si el `CircuitBreaker` debía abrirse si la renovación del token de seguridad fallaba con un error HTTP 401. Uno de los integrantes proponía contar el 401 como un fallo de red tradicional.

**Resolución técnica:** Tras analizar los invariantes de seguridad, determinamos que un error 401 indica una credencial inválida o expirada (problema de sesión/identidad), no una degradación de la infraestructura de red. Si permitíamos que el 401 abriera el circuito, un atacante enviando tokens corruptos de forma masiva provocaría una Denegación de Servicio (DoS) local, abriendo el circuito para todos los usuarios legítimos. Por ende, se implementó el filtro inteligente en el bloque `except` del breaker para hacer bypass inmediato a las excepciones de autenticación (cumpliendo con el requerimiento **INV-A4**).
