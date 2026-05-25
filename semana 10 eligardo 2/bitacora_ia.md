# Bitácora de Uso de IA - Evaluación de Arquitectura

**1. Prompt usado:**
> Actúa como comité de revisión arquitectónica. Mi ADR trata sobre la decisión de excluir las peticiones de Autenticación del Circuit Breaker principal para separar responsabilidades. Presenta un escenario concreto de EcoMarket donde mi decisión produce un resultado peor que la alternativa rechazada.

**2. Respuesta relevante resumida (IA):**
La IA actuó como abogado del diablo y planteó un escenario de "Black Friday" donde la API de Inventario y Autenticación comparten el mismo servidor físico que sufre una sobrecarga. Cuestionó qué pasaría si la ruta de auth queda desprotegida ante múltiples reintentos de los clientes.

**3. Decisión que aceptaste/rechazaste y justificación:**
**Acepté la retroalimentación.** Inicialmente deduje que la única consecuencia era que "nadie pasaría" al sistema. Sin embargo, a través del intercambio socrático, integré la perspectiva de infraestructura: la falta de un Circuit Breaker en la autenticación provoca un efecto de "Cascading Failure". Los clientes saturarían el servidor caído con intentos de conexión infinitos, empeorando el cuello de botella.



# Bitácora de Uso de IA - Evaluación de Estrategia SSE vs CB

**1. Prompt usado:**
> Actúa como arquitecto de AWS especialista en e-commerce. EcoMarket tiene 1,200 operadores simultáneos en Black Friday. El servidor de inventario falla (CB abre por 60 s), pero el servidor SSE de alertas es un servicio separado y sigue funcionando. Mi argumento es a favor de la Estrategia B (SSE independiente reconecta inmediatamente). Presenta el contra-argumento más fuerte y pregunta qué pasa si comparten host.

**2. Respuesta relevante resumida (IA):**
La IA señaló el riesgo del "Rebaño en Estampida" (Thundering Herd). Si 1,200 clientes reconectan su SSE instantáneamente ante un micro-corte, podrían agotar los hilos del servidor sano. Además, cuestionó la viabilidad de la Estrategia B si resulta que, por costos, la API HTTP y el servidor SSE comparten el mismo host físico.

**3. Decisión que aceptaste/rechazaste y justificación:**
**Mantuve la Estrategia B, pero acepté el trade-off y la condición de infraestructura.** Si el HTTP y el SSE comparten host físico, la Estrategia B sería peligrosa porque los intentos de reconexión asfixiarían el servidor caído, previniendo su recuperación. Sin embargo, para EcoMarket en Black Friday, la consistencia de datos es vital para evitar sobreventas. La decisión final es mantener la Estrategia B (reconectar independientemente del Circuit Breaker HTTP), pero con el prerrequisito arquitectónico de que **deben estar en hosts separados** y el cliente debe implementar un "Exponential Backoff" (retraso progresivo) en sus intentos de reconexión para no tumbar al servidor SSE con picos de tráfico.