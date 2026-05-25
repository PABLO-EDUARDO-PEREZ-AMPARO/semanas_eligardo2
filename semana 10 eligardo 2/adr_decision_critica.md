# ADR 001: Exclusión de la Autenticación del Circuit Breaker

**Estado:** Aceptado
**Fecha:** Mayo 2026

## 1. Contexto y Problema
El sistema requiere manejar tokens de seguridad (JWT) de corta duración y proteger las llamadas de red usando un patrón Circuit Breaker. El problema arquitectónico principal era decidir si las peticiones de renovación de token (`refresh_access_token`) debían pasar a través del Circuit Breaker principal o ejecutarse por fuera de su protección.

## 2. Decisión
Se decidió **excluir** el servicio de Autenticación (`TokenManager`) del `CircuitBreaker` que protege al servicio de negocio (Inventario/E-commerce). El orquestador (`ClienteRobusto`) tiene la responsabilidad estricta de validar y renovar el token *antes* de invocar la ejecución protegida por el circuito.

## 3. Justificación (Escenario Adverso)
Si el `TokenManager` estuviera sujeto al estado del `CircuitBreaker`, ocurriría un bloqueo irrecuperable ("Deadlock de resiliencia"). 

**Escenario adverso evaluado:**
1. El servidor de Inventario se cae. El Circuit Breaker registra 3 fallos y cambia a estado `ABIERTO`.
2. Pasan los 5 segundos de timeout y el circuito cambia a `SEMIABIERTO`. Está listo para enviar *una sola petición piloto*.
3. Sin embargo, durante ese tiempo, el token JWT expiró.
4. Si la petición viaja con el token caducado, el servidor la rechazará con un `HTTP 401 Unauthorized`.
5. El Circuit Breaker interpretará el 401 como un fallo del piloto y regresará a estado `ABIERTO`, aunque la red y el inventario ya estén sanos. El sistema nunca se recuperaría de forma natural.

Al separar las responsabilidades, garantizamos que la petición piloto viaje siempre con credenciales frescas y valide la salud real de la infraestructura, no el estado de la sesión local.

## 4. Consecuencias
* **Positivas:** Prevención del Thundering Herd en SEMIABIERTO, recuperación garantizada del circuito y cumplimiento estricto del principio de Responsabilidad Única (SRP).
* **Negativas:** El endpoint de autenticación no goza de la protección de "fallo rápido" local, por lo que si el servidor de Auth se cae, el cliente experimentará la latencia real de red (timeout del cliente HTTP) en la llamada de refresh.