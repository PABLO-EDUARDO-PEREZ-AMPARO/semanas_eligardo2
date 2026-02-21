import asyncio
import time
import random

# --- 1. LIMITADOR DE CONCURRENCIA (SEMÁFORO) ---
class LimitadorConcurrencia:
    def __init__(self, max_concurrent):
        self.sem = asyncio.Semaphore(max_concurrent)
        self.max = max_concurrent
    
    async def __aenter__(self):
        # Intentamos entrar al carril
        await self.sem.acquire()
        # Retornamos self para poder usar métodos si fuera necesario
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # Salimos del carril, liberando espacio para otro
        self.sem.release()

# --- 2. LIMITADOR DE TASA (TOKEN BUCKET) ---
class LimitadorTasa:
    def __init__(self, rate_per_second):
        self.rate = rate_per_second
        self.tokens = rate_per_second # Empezamos con el cubo lleno
        self.capacity = rate_per_second
        self.last_check = time.monotonic()
        self.lock = asyncio.Lock() # Para evitar condiciones de carrera

    async def __aenter__(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_check
            self.last_check = now
            
            # 1. Rellenar el cubo (Refill)
            # Calculamos cuántos tokens se generaron en este tiempo
            new_tokens = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            
            # 2. Consumir token
            if self.tokens < 1:
                # No hay tokens, hay que esperar a que se genere 1
                wait_time = (1 - self.tokens) / self.rate
                print(f"   💧 [RateLimit] Frenando... Esperando {wait_time:.3f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 0 # Consumimos el que acabamos de generar
            else:
                self.tokens -= 1 # Consumimos 1 token existente

    async def __aexit__(self, exc_type, exc, tb):
        pass

# --- 3. CLIENTE ESTRANGULADO (THROTTLED CLIENT) ---
class ClienteControlado:
    def __init__(self, max_concurrent=10, max_per_sec=20):
        self.concurrency = LimitadorConcurrencia(max_concurrent)
        self.rate_limit = LimitadorTasa(max_per_sec)
        self.active_requests = 0 # Solo para estadísticas

    async def solicitar(self, pid):
        # APLICAMOS DOBLE CAPA DE PROTECCIÓN
        
        # Capa 1: Semáforo (¿Hay carriles libres?)
        async with self.concurrency:
            # Capa 2: Tasa (¿Vamos muy rápido?)
            async with self.rate_limit:
                
                # --- ZONA CRÍTICA (Simulación de Request) ---
                self.active_requests += 1
                # print(f"🚀 [POST] Prod-{pid} en vuelo (Activos: {self.active_requests})")
                
                start = time.perf_counter()
                
                # Simulamos latencia de red variable (0.1 a 0.5s)
                # Si fuera real, aquí iría: await session.post(...)
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
                self.active_requests -= 1
                return f"Prod-{pid} Creado"

# --- 4. TEST DE ESTRÉS ---
async def test_traffic_control():
    # CONFIGURACIÓN DEL EXPERIMENTO
    N_PETICIONES = 50
    MAX_CONCURRENT = 10
    MAX_PER_SEC = 20  # Límite de velocidad
    
    print(f"🚦 INICIANDO PRUEBA DE ESTRÉS")
    print(f"   - Total Peticiones: {N_PETICIONES}")
    print(f"   - Max Simultáneas:  {MAX_CONCURRENT} (Semáforo)")
    print(f"   - Max por Segundo:  {MAX_PER_SEC} (Token Bucket)")
    print("-" * 40)

    cliente = ClienteControlado(MAX_CONCURRENT, MAX_PER_SEC)
    start_global = time.perf_counter()

    # Función auxiliar para monitorizar concurrencia real
    async def monitor():
        max_seen = 0
        while True:
            current = cliente.active_requests
            if current > max_seen: max_seen = current
            # Si vemos más de 10, fallamos el test
            if current > MAX_CONCURRENT:
                print(f"💀 ¡ALERTA! Se violó el límite de concurrencia: {current}")
            await asyncio.sleep(0.01)
            # Detenemos monitor si ya acabaron todos (truco sucio para demo)
            if time.perf_counter() - start_global > 5 and current == 0:
                break
        return max_seen

    # Lanzamos el monitor en paralelo
    monitor_task = asyncio.create_task(monitor())

    # Lanzamos las 50 peticiones de golpe
    tareas = [cliente.solicitar(i) for i in range(N_PETICIONES)]
    
    # Gather espera a todas
    await asyncio.gather(*tareas)
    
    end_global = time.perf_counter()
    duration = end_global - start_global
    
    # Cancelamos monitor
    monitor_task.cancel()
    try: await monitor_task
    except asyncio.CancelledError: pass

    # --- RESULTADOS ---
    rps_real = N_PETICIONES / duration
    
    print("-" * 40)
    print("📊 REPORTE FINAL DE TRÁFICO")
    print("-" * 40)
    print(f"✅ Tiempo Total:      {duration:.2f} segundos")
    print(f"✅ Velocidad Real:    {rps_real:.2f} req/s")
    print(f"✅ Límite Config:     {MAX_PER_SEC} req/s")
    
    if rps_real <= MAX_PER_SEC + 2: # Margen de error pequeño aceptable
        print("🏆 PRUEBA SUPERADA: Se respetó el límite de velocidad.")
    else:
        print("❌ FALLO: Fuiste demasiado rápido.")

if __name__ == "__main__":
    try:
        asyncio.run(test_traffic_control())
    except KeyboardInterrupt:
        pass