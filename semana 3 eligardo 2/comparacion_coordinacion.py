import asyncio
import time

# --- MOCK DE ENDPOINTS ---
async def fetch_api(name, delay, fail=False):
    await asyncio.sleep(delay)
    if fail:
        raise RuntimeError(f"Fallo crítico en {name}")
    return f"Result:{name}"

async def limpiar_tareas(tareas):
    """Invariante #3: Cleanup de tareas pendientes"""
    for t in tareas:
        if not t.done():
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass

# --- ESTRATEGIAS ---

async def test_gather(tasks_data):
    print("\n--- Probando GATHER (Todo o nada) ---")
    start = time.perf_counter()
    tasks = [fetch_api(n, d, f) for n, d, f in tasks_data]
    
    # Invariante #2: return_exceptions=True
    resultados = await asyncio.gather(*tasks, return_exceptions=True)
    
    end = time.perf_counter()
    print(f"✅ Dashboard cargado. Tiempo total: {end-start:.3f}s")
    return end - start

async def test_as_completed(tasks_data):
    print("\n--- Probando AS_COMPLETED (Streaming) ---")
    start = time.perf_counter()
    tasks = [fetch_api(n, d, f) for n, d, f in tasks_data]
    
    tiempos_llegada = []
    for i, coro in enumerate(asyncio.as_completed(tasks)):
        try:
            res = await coro
            tiempos_llegada.append(time.perf_counter() - start)
            if i == 0: print(f"🚀 Primer dato a los: {tiempos_llegada[0]:.3f}s")
        except Exception as e:
            print(f"⚠️ Error capturado: {e}")
            
    end = time.perf_counter()
    print(f"✅ Dashboard cargado. Tiempo total: {end-start:.3f}s")
    return tiempos_llegada[0], end - start

async def test_wait_first(tasks_data):
    print("\n--- Probando WAIT (FIRST_COMPLETED) ---")
    start = time.perf_counter()
    # Creamos objetos Task reales
    tasks = [asyncio.create_task(fetch_api(n, d, f)) for n, d, f in tasks_data]
    
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    
    ttf = time.perf_counter() - start
    print(f"🚀 Control recuperado al primer dato: {ttf:.3f}s")
    
    # Limpiamos lo que quedó pendiente para no dejar resource leaks (Invariante #3)
    await limpiar_tareas(pending)
    return ttf

async def main():
    # Escenario: Perfil(0.2s), Productos(0.5s), Carrito(1.0s), Ads(Lento 3s o Fallo)
    escenario = [
        ("Perfil", 0.2, False),
        ("Productos", 0.5, False),
        ("Carrito", 1.0, False),
        ("Anuncios", 3.0, True) # Este es el que nos frena
    ]
    
    print("🧪 INICIANDO COMPARATIVA DE COORDINACIÓN")
    t_gather = await test_gather(escenario)
    ttf_as, total_as = await test_as_completed(escenario)
    ttf_wait = await test_wait_first(escenario)

    print("\n" + "="*40)
    print("📊 RESUMEN PARA ECO-MARKET")
    print("="*40)
    print(f"Estrategia Gather  | Total: {t_gather:.3f}s | TTF: {t_gather:.3f}s")
    print(f"Estrategia Stream  | Total: {total_as:.3f}s | TTF: {ttf_as:.3f}s")
    print(f"Estrategia Wait    | Total: {ttf_wait:.3f}s | TTF: {ttf_wait:.3f}s (Abortado)")

if __name__ == "__main__":
    asyncio.run(main())