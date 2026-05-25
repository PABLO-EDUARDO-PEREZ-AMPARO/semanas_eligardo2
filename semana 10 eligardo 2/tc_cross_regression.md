# 🧪 Casos de Prueba de Regresión Cruzada (TC-X)

## TC-X1: SSE activo + Circuit Breaker transiciona a ABIERTO
* **Setup:** Se inicia el `ClienteSSEMultiplex` con conexión establecida al servidor de alertas. En paralelo, se inyecta un mock en el `ClienteRobusto` (HTTP) configurado para retornar HTTP 503.
* **Acción:** Se disparan 5 peticiones HTTP simultáneas, superando el umbral del `CircuitBreaker` y forzando su estado a `ABIERTO`. Simultáneamente, el servidor emite un evento SSE.
* **Verificación:** Se evalúa si el `EventRouter` recibe el evento en tiempo real o si es bloqueado por el estado del CB.
* **Resultado:** ✅ **PASS**. La conexión SSE no se interrumpe. El CB actúa exclusivamente sobre la capa de peticiones HTTP (ciclo corto) sin afectar el túnel TCP activo del SSE.

## TC-X2: Token expira mientras CB en SEMIABIERTO
* **Evidencia Automatizada:** Ejecutada en `test_tc_x2_refresh_semiabierto.py`.
* **Setup:** Mock del `TokenManager` configurado para retornar `True` en `is_expiring_soon()`. `CircuitBreaker` forzado a estado `SEMIABIERTO`.
* **Acción:** Se invoca la función de ejecución principal del cliente.
* **Verificación:** Se cuentan y ordenan las invocaciones.
* **Resultado:** ✅ **PASS**. El orden de ejecución es estrictamente `["REFRESH", "PILOTO_HTTP"]`. 
* **Justificación:** Si el piloto viajara primero y el token estuviera vencido, el servidor rechazaría la petición (HTTP 401). Esto desperdiciaría la prueba de red del estado SEMIABIERTO en un error local de sesión.

## TC-X3: Reconexión SSE con Last-Event-ID tras cierre del circuito
* **Setup:** Se simula un corte total de red. CB pasa a `ABIERTO` y SSE se desconecta. El último evento recibido fue `msg-99`.
* **Acción:** Transcurre el timeout (60s). El CB se cierra. El auto-recolector del SSE inicia el handshake de reconexión.
* **Verificación:** Se inspeccionan los headers HTTP enviados en la reconexión.
* **Resultado:** ✅ **PASS**. El header `Last-Event-ID: msg-99` se incluye correctamente y no se resetea. Además, la conexión se realiza utilizando el token de acceso más reciente provisto por el `TokenManager`.