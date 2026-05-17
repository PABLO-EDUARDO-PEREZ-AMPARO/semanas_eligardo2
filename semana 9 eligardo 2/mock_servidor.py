# mock_servidor.py — Simula fallos del servidor para probar el CircuitBreaker
import asyncio
import aiohttp
from aiohttp import web

class ServidorMockEcoMarket:
    """
    Servidor mock que simula modos de fallo configurables.
    
    Uso:
        mock = ServidorMockEcoMarket()
        mock.modo = 'normal'     # Responde 200
        mock.modo = 'fallo_503'  # Responde 503
        mock.modo = 'timeout'    # No responde (simula timeout)
        mock.modo = 'auth'       # Responde 401
    """
    def __init__(self):
        self.modo = 'normal'
        self._peticiones_recibidas = 0
        self.app = web.Application()
        self.app.router.add_get('/api/inventario', self._handler)
        self.app.router.add_post('/api/auth/token', self._handler_auth)

    async def _handler(self, request):
        self._peticiones_recibidas += 1
        print(f"[MOCK] Petición #{self._peticiones_recibidas} | modo={self.modo}")

        if self.modo == 'fallo_503':
            return web.Response(status=503, text='Service Unavailable')
        elif self.modo == 'timeout':
            await asyncio.sleep(60)  # El cliente hará timeout primero
            return web.Response(status=200, text='tardísimo')
        elif self.modo == 'auth':
            return web.Response(status=401, text='Unauthorized')
        else:  # normal
            return web.json_response({'productos': 42, 'timestamp': 'ahora'})

    async def _handler_auth(self, request):
        return web.json_response({
            'access_token': 'mock.token.aqui',
            'refresh_token': 'mock.refresh.aqui',
            'expires_in': 900
        })

    @property
    def peticiones_recibidas(self) -> int:
        return self._peticiones_recibidas


# Demo de prueba rápida
async def demo():
    mock = ServidorMockEcoMarket()
    runner = web.AppRunner(mock.app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    print("[MOCK] Servidor activo en http://localhost:8080")

    # Aquí conectas tu ClienteRobusto y cambias mock.modo para simular fallos
    # mock.modo = 'fallo_503'
    await asyncio.sleep(3600)  # Servidor activo 1 hora para pruebas

if __name__ == '__main__':
    asyncio.run(demo())