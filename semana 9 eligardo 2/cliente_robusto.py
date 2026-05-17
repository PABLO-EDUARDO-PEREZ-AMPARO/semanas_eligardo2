"""
cliente_robusto.py — Integración del ClienteRobusto para EcoMarket
Semana 9: Resiliencia y Tolerancia a Fallos

ORDEN DE CAPAS IMPLEMENTADO:
1. Capa Exterior: CircuitBreaker (Fail Fast, bloquea antes de gastar recursos).
2. Capa Media: TokenManager (Prepara/Renueva token solo si el circuito está CERRADO).
3. Capa Interior: ClienteSSEMultiplex (Ejecuta la llamada de red HTTP).
"""

import asyncio
import aiohttp
from aiohttp import web
from circuit_breaker import CircuitBreaker, CircuitOpenError
from mock_servidor import ServidorMockEcoMarket

# ==========================================
# 1. COMPONENTES SIMULADOS (Mock)
# ==========================================
class TokenManagerMock:
    async def obtener_token(self):
        # Simula la obtención o renovación del JWT
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

class ClienteSSEMultiplexMock:
    async def conectar(self, session: aiohttp.ClientSession, url: str, token: str):
        # Simula el viaje por la red inyectando las credenciales
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(url, headers=headers) as response:
            # vital: Lanza un aiohttp.ClientResponseError si el status es 4xx o 5xx.
            # Nuestro CircuitBreaker leerá el atributo '.status' de este error.
            response.raise_for_status() 
            return await response.json()


# ==========================================
# 2. EL CLIENTE ROBUSTO (Megazord)
# ==========================================
class ClienteRobusto:
    def __init__(self, umbral_fallos: int = 5, timeout_apertura: float = 60.0):
        # Inyectamos las dependencias
        self.cb = CircuitBreaker(umbral_fallos=umbral_fallos, timeout_apertura=timeout_apertura)
        self.token_manager = TokenManagerMock()
        self.sse = ClienteSSEMultiplexMock()

    async def obtener_inventario(self, session: aiohttp.ClientSession, url: str):
        """Misión que envuelve el proceso completo bajo la protección del Circuit Breaker."""
        
        async def mision_interna():
            # Capa 2: Preparamos pasaporte
            token = await self.token_manager.obtener_token()
            # Capa 3: Viaje en avión
            return await self.sse.conectar(session, url, token)

        # Capa 1: El guardia de seguridad envuelve la misión
        return await self.cb.ejecutar(mision_interna())


# ==========================================
# 3. DEMOSTRACIÓN (Para demo_resiliencia.log)
# ==========================================
async def demo_resiliencia():
    print("=== INICIANDO DEMO DE RESILIENCIA ===")
    
    # Arrancamos el servidor mock en segundo plano (puerto 8080)
    mock_server = ServidorMockEcoMarket()
    runner = web.AppRunner(mock_server.app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    
    url = "http://localhost:8080/api/inventario"
    
    # Instanciamos con 5 segundos de timeout para que el demo sea ágil
    cliente = ClienteRobusto(umbral_fallos=5, timeout_apertura=5.0)

    async with aiohttp.ClientSession() as session:
        # --- (1) MODO NORMAL ---
        print("\n--- FASE 1: MODO NORMAL (3 peticiones exitosas) ---")
        mock_server.modo = 'normal'
        for i in range(3):
            res = await cliente.obtener_inventario(session, url)
            print(f"✅ Petición {i+1} Exitosa: {res}")
            await asyncio.sleep(0.5)

        # --- (2) MODO FALLO_503 ---
        print("\n--- FASE 2: MODO FALLO_503 (Colapso del servidor) ---")
        mock_server.modo = 'fallo_503'
        
        # Hacemos 6 intentos: Los primeros 5 golpean al servidor. El 6to sufre Fail-Fast.
        for i in range(6): 
            try:
                print(f"Intentando petición {i+1} en plena crisis...")
                await cliente.obtener_inventario(session, url)
            except CircuitOpenError as e:
                print(f"🛡️ FAIL-FAST / CORTOCIRCUITO: {e}")
            except Exception as e:
                print(f"❌ Error HTTP real recibido: {e}")
            await asyncio.sleep(0.5)

        # --- (3) ESPERANDO TIMEOUT ---
        print("\n--- FASE 3: ESPERANDO TIMEOUT (5 segundos) ---")
        print("Circuito abierto. Dando tiempo al servidor para que respire...")
        for i in range(5, 0, -1):
            print(f"⏳ {i}...")
            await asyncio.sleep(1)

        # --- (4) RESTAURAR MODO NORMAL ---
        print("\n--- FASE 4: RECUPERACIÓN (Servidor Normalizado) ---")
        mock_server.modo = 'normal'
        
        try:
            print("Enviando petición exploradora (Estado Semiabierto)...")
            res = await cliente.obtener_inventario(session, url)
            print(f"✅ Petición exploradora triunfó: {res}")
        except Exception as e:
            print(f"Error: {e}")

        try:
            print("Enviando petición de confirmación (Circuito Cerrado)...")
            res = await cliente.obtener_inventario(session, url)
            print(f"✅ Petición confirmada: {res}")
        except Exception as e:
            print(f"Error: {e}")

    # Apagamos el servidor mock limpiamente
    await runner.cleanup()
    print("\n=== FIN DE LA DEMO ===")

if __name__ == '__main__':
    asyncio.run(demo_resiliencia())