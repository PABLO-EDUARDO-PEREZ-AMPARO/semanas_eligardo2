Arquitectura de Múltiples Circuit Breakers (Bulkhead Pattern)
Este documento detalla la implementación avanzada del ClienteRobusto para EcoMarket, pasando de un enfoque de "Breaker Global" a una arquitectura de "Breaker por Dominio/API" (Bulkhead Pattern). Esto garantiza que un fallo en un servicio frágil (como Inventario) no afecte la disponibilidad de servicios estables (como Precios).

1. Diagrama ASCII de la Arquitectura
Plaintext
       ┌─────────────────────────────────────────────────────────┐
       │              CLIENTE ROBUSTO (EcoMarket API)             │
       │                                                         │
       │  ┌─────────────────────┐       ┌──────────────────────┐ │
       │  │    TokenManager     │       │ Interceptor HTTP (S7)│ │
       │  │ (Auth & Refresh)    │◀─────▶│ (Inyecta JWT)        │ │
       │  └──────────┬──────────┘       └───────────▲──────────┘ │
       │             │ Bypass                      │             │
       │             └────────┐                    │             │
       │                      ▼                    │             │
       │           ┌──────────────────────┐        │             │
       │           │  get("/api/auth")    │────────┘             │
       │           └──────────────────────┘                      │
       │                                                         │
       │─────────────────────────────────────────────────────────│
       │                    REGISTRO DE BREAKERS                 │
       │                                                         │
       │  1. get("/inventario")                                  │
       │       ▼                                                 │
       │    ┌───────────────────┐    ┌────────────────────┐      │
       │    │ CB - Inventario   │───▶│ Sesión HTTP (aio)  │────▶ EcoMarket
       │    │ (Frágil: 5 attempts)│    └────────────────────┘      API
       │    └───────────────────┘                                (Net)
       │                                                         │
       │  2. get("/precios")                                     │
       │       ▼                                                 │
       │    ┌───────────────────┐    ┌────────────────────┐      │
       │    │ CB - Precios      │───▶│ Sesión HTTP (aio)  │────▶ Externo
       │    │ (Estable: 3 attempts)│    └────────────────────┘      API
       │    └───────────────────┘                                (Net)
       │                                                         │
       └─────────────────────────────────────────────────────────┘
2. Pseudocódigo de Implementación
(1) Dónde se crean los breakers y (2) Cómo se seleccionan
La creación de los breakers ocurre una sola vez en el constructor (__init__) del ClienteRobusto, encapsulando la lógica de la clase CircuitBreaker sin duplicar código.

Python
class ClienteRobusto:
    """
    Cliente API con compartimentación de fallos (Bulkhead).
    Utiliza instancias independientes de la clase genérica CircuitBreaker.
    """
    def __init__(self, token_manager, timeout_red=1.5):
        self.token_manager = token_manager
        self.timeout_red = timeout_red # Timeout estricto para forzar fallos lentos
        
        # --- (1) CREACIÓN DE BREAKERS INDEPENDIENTES ---
        # Configuramos umbrales y tiempos específicos para cada perfil de riesgo.
        self._cb_inventario = CircuitBreaker(
            umbral_fallos=5, 
            timeout_apertura=15.0, # Apertura corta para detección rápida de restart (E1)
            nombre="EcoMarket-Inventario"
        )
        
        self._cb_precios = CircuitBreaker(
            umbral_fallos=3, # Es muy estable, reaccionamos más rápido al fallo.
            timeout_apertura=30.0, # Timeout largo, el servicio externo tarda más en volver.
            nombre="Servicio-Precios-Externo"
        )
        # -----------------------------------------------

    async def obtener_inventario(self):
        """Endpoint frágil. Protegido por su propio breaker."""
        # --- (2) SELECCIÓN DEL BREAKER ---
        # La llamada de red se envuelve explícitamente en el breaker de inventario.
        coro_red = self._cliente_http.get("/api/inventario", timeout=self.timeout_red)
        
        try:
            return await self._cb_inventario.ejecutar(coro_red)
        except CircuitOpenError:
            # Fallback: leer del caché SSE multiplexado (S7).
            print("⚠️ Circuit Breaker de Inventario ABIERTO. Usando fallback de caché SSE.")
            return self.cacche_sse.get_last_known_inventory()

    async def obtener_precios(self):
        """Endpoint estable. Protegido por su propio breaker."""
        # --- (2) SELECCIÓN DEL BREAKER ---
        # Aunque el inventario esté caído, este breaker permanece CERRADO.
        coro_red = self._cliente_http.get("/api/precios", timeout=self.timeout_red)
        
        return await self._cb_precios.ejecutar(coro_red)
3. Decisión de Diseño: Tráfico de Autenticación (POST /api/auth)
Decisión: BYPASS COMPLETO del sistema de Circuit Breakers.

Justificación Documentada:
Como se visualiza en el diagrama ASCII, el tráfico generado por el TokenManager para obtener o renovar el JWT (Bypass) no utiliza ninguna instancia de CircuitBreaker.

Prevención de Deadlock: Si el servidor de autenticación compartiera el breaker con el de inventario, una caída del inventario bloquearía la renovación de tokens. Al pasar a SEMIABIERTO, la petición de prueba de inventario fallaría con un 401 Unauthorized porque el token no pudo renovarse, impidiendo que el circuito principal cerrara nunca (deadlock).

Dominios de Fallo Distintos: El servidor de autenticación y la API de negocio son infraestructuras independientes. Un fallo en uno no implica un fallo en el otro.

Autonomía del TokenManager: El TokenManager debe ser autónomo en su resiliencia elemental (manejando sus propios timeouts de red), garantizando que siempre haya un token fresco disponible para que los Circuit Breakers de negocio puedan evaluar la salud real de sus servidores sin interferencia de errores de credenciales.