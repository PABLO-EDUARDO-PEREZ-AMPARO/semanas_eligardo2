import asyncio
import time
import random

# --- 1. LIMITADOR DE CONCURRENCIA ---
class ConcurrencyLimiter:
    def __init__(self, n):
        self.semaphore = asyncio.Semaphore(n)

    async def acquire(self):
        await self.semaphore.acquire()

    def release(self):
        self.semaphore.release()

# --- 2. LIMITADOR DE TASA (TOKEN BUCKET) ---
class RateLimiter:
    def __init__(self, rps):
        self.rps = rps
        self.tokens = rps
        self.last_update = time.monotonic()

    async def wait(self):
        while True:
            now = time.monotonic()
            # Rellenar tokens según el tiempo pasado
            self.tokens += (now - self.last_update) * self.rps
            self.last_update = now
            
            if self.tokens > self.rps: self.tokens = self.rps
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            await asyncio.sleep(0.05) # Espera breve para reintentar

# --- 3. CLIENTE CONTROLADO ---
class ThrottledClient:
    def __init__(self, max_concurrent, max_rps):
        self.c_limiter = ConcurrencyLimiter(max_concurrent)
        self.r_limiter = RateLimiter(max_rps)
        self.in_flight = 0 # Contador para la gráfica

    async def request(self, id):
        # Aplicamos ambos límites
        await self.c_limiter.acquire() # ¿Hay carril libre?
        try:
            await self.r_limiter.wait() # ¿Podemos acelerar?
            
            # --- Inicio de Petición ---
            self.in_flight += 1
            # Simulamos que la petición tarda entre 0.5 y 1 segundo
            await asyncio.sleep(random.uniform(0.5, 1.0))
            self.in_flight -= 1
            # --- Fin de Petición ---
            
            return f"Respuesta {id}"
        finally:
            self.c_limiter.release()

# --- MONITOREO Y TEST ---
async def generar_reporte():
    print("🚦 INICIANDO TEST DE TRÁFICO (50 Peticiones)...")
    client = ThrottledClient(max_concurrent=10, max_rps=20)
    
    # Lista para guardar datos de la gráfica: (tiempo, peticiones_en_vuelo)
    stats = []
    start_time = time.monotonic()

    async def monitor():
        while True:
            t = round(time.monotonic() - start_time, 1)
            stats.append((t, client.in_flight))
            await asyncio.sleep(0.2)
            if t > 5: break # Detener monitoreo después de 5s

    # Lanzamos 50 peticiones
    tasks = [asyncio.create_task(client.request(i)) for i in range(50)]
    monitor_task = asyncio.create_task(monitor())

    await asyncio.gather(*tasks)
    monitor_task.cancel()

    # --- GENERAR TABLA PARA EL ENTREGABLE ---
    print("\n📊 DATOS PARA LA GRÁFICA (Peticiones en vuelo vs Tiempo)")
    print("| Tiempo (s) | Pets. en Vuelo | Estado |")
    print("|------------|----------------|--------|")
    for t, count in stats[::2]: # Mostramos cada 0.4s para brevedad
        estado = "🟡 Llenando" if count < 10 else "🟢 LÍMITE (MAX)"
        print(f"| {t:9.1f} | {count:14} | {estado} |")

if __name__ == "__main__":
    asyncio.run(generar_reporte())