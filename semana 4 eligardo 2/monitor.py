"""
Documento de Decisiones (Trade-offs):
1. Bloqueo Síncrono: Los observadores se ejecutan secuencialmente. Si uno es lento, retrasa el polling.
2. Sin límite de reintentos: El backoff llega a 60s, pero no se apaga solo tras múltiples fallos 5xx.
3. Timeout estático: Usamos 10s para Short Polling; habría que aumentarlo drásticamente para Long Polling.
"""

import asyncio
import aiohttp
import datetime

ServicioWebSocket : Observable

# ==========================================
# 1. CLASE OBSERVABLE (La base)
# ==========================================
class Observable:
    def __init__(self):
        self._observadores = []

    def agregar_observador(self, observador):
        if observador not in self._observadores:
            self._observadores.append(observador)

    def notificar(self, datos):
        for observador in self._observadores:
            observador(datos)

# ==========================================
# 2. EL SERVICIO DE WEBSOCKET (El motor)
# ==========================================
class ServicioWebSocket(Observable):
    def __init__(self):
        super().__init__()
        self._intervalo = 5       # Inicia en 5 segundos
        self._etag = None         # Memoria del último ETag
        self._activo = False

    async def _consultar(self, session):
        url = "http://localhost:9999/productos/500"
        headers = {}
        if self._etag:
            headers["If-None-Match"] = self._etag

        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    self._etag = resp.headers.get("ETag", self._etag)
                    datos = await resp.json()
                    
                    # Convertimos a lista si es un solo dict para facilitar a los observadores
                    if isinstance(datos, dict) and "id" in datos:
                        datos = [datos]

                    self.notificar(datos)
                    self._intervalo = max(5, self._intervalo - 5)
                    print(f"🔄 [HTTP 200] Cambio detectado. Intervalo reducido a: {self._intervalo}s")

                elif resp.status == 304:
                    self._intervalo = min(60, self._intervalo + 5)
                    print(f"💤 [HTTP 304] Sin cambios. Intervalo aumentado a: {self._intervalo}s")

                elif resp.status >= 500:
                    self._intervalo = min(60, self._intervalo + 10)
                    print(f"⚠️ [HTTP {resp.status}] Servidor fallando. Backoff a: {self._intervalo}s")

        except asyncio.TimeoutError:
            self._intervalo = min(60, self._intervalo + 10)
            print(f"⏳ [TIMEOUT] El servidor no respondió. Backoff a: {self._intervalo}s")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")

    async def iniciar(self):
        self._activo = True
        print("🚀 Iniciando Monitor de Inventario EcoMarket...")
        
        async with aiohttp.ClientSession() as session:
            while self._activo:
                await self._consultar(session)
                print(f"⏳ Esperando {self._intervalo} segundos...\n")
                await asyncio.sleep(self._intervalo)

    def detener(self):
        self._activo = False
        print("🛑 Deteniendo Monitor...")

# ==========================================
# 3. LOS OBSERVADORES (Las funciones independientes)
# ==========================================
def imprimir_actualizados(datos):
    print(f"🖥️  [UI] Pantalla actualizada. Mostrando {len(datos)} productos.")

def detectar_agotados(datos):
    if not datos: return
    for producto in datos:
        # Simulamos que si el ID es 999 o stock es 0, hay alerta
        if producto.get("stock") == 0 or producto.get("disponible") is False:
            nombre = producto.get("nombre", "Desconocido")
            print(f"🚨 [ALERTA] ¡El producto '{nombre}' se ha agotado!")

def registrar_log(datos):
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"📝 [{hora}] Datos procesados correctamente en sistema.")

# ==========================================
# 4. BLOQUE PRINCIPAL DE EJECUCIÓN
# ==========================================
async def main():
    monitor = ServicioWebSocket()
    
    # Conectando cables (Patrón Observer)
    monitor.agregar_observador(imprimir_actualizados)
    monitor.agregar_observador(detectar_agotados)
    monitor.agregar_observador(registrar_log)

    # Creamos una tarea para que el monitor corra en el fondo
    tarea_monitor = asyncio.create_task(monitor.iniciar())

    # Dejamos que corra por 30 segundos (unos 5-6 ciclos) para la demostración
    await asyncio.sleep(30)
    
    # Detenemos todo limpiamente
    monitor.detener()
    await tarea_monitor

if __name__ == "__main__":
    asyncio.run(main())