from circuit_breaker import CircuitBreaker
from token_manager import TokenManager

class ClienteRobusto:
    def __init__(self, umbral_cb=3, timeout_cb=5):
        self.cb = CircuitBreaker(umbral=umbral_cb, timeout=timeout_cb)
        self.tm = TokenManager()

    async def ejecutar_peticion(self, funcion_http):
        # 1. Asegurar credenciales vigentes antes de intentar tocar la red
        if self.tm.is_expiring_soon():
            await self.tm.refresh_access_token()
        
        # 2. Ejecutar de forma segura bajo la protección del breaker
        return await self.cb.ejecutar(funcion_http)