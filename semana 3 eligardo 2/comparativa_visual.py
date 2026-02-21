import asyncio
import aiohttp
import time

# --- 1. EL RIVAL LENTO (Simulación Síncrona) ---
def ejecutar_dashboard_sincrono():
    print("\n🐢 --- MODO SÍNCRONO (Bloqueante) ---")
    inicio = time.perf_counter()
    
    # En modo síncrono, si una tarea tarda, todo se detiene
    print("   ⏳ [1/3] Pidiendo Productos... (esperando respuesta)")
    time.sleep(0.5) # Simula latencia de red real
    
    print("   ⏳ [2/3] Pidiendo Categorías... (esperando respuesta)")
    time.sleep(0.5) 
    
    print("   ⏳ [3/3] Pidiendo Perfil... (esperando respuesta)")
    time.sleep(0.3)
    
    fin = time.perf_counter()
    tiempo = fin - inicio
    print(f"🐢 TERMINADO. Tiempo total: {tiempo:.2f} segundos")
    return tiempo

# --- 2. EL HÉROE RÁPIDO (Tu código Asíncrono) ---
async def ejecutar_dashboard_asincrono():
    print("\n🚀 --- MODO ASÍNCRONO (No Bloqueante) ---")
    inicio = time.perf_counter()
    
    # Aquí definimos las tareas, pero NO esperamos una por una
    async with aiohttp.ClientSession() as session:
        # Simulamos las mismas peticiones pero usando aiohttp
        t1 = simular_peticion(session, 0.5, "Productos")
        t2 = simular_peticion(session, 0.5, "Categorías")
        t3 = simular_peticion(session, 0.3, "Perfil")
        
        print("   ⚡ ¡Lanzando las 3 peticiones a la vez!")
        # await gather espera a que acabe la más lenta, no la suma de todas
        await asyncio.gather(t1, t2, t3)
    
    fin = time.perf_counter()
    tiempo = fin - inicio
    print(f"🚀 TERMINADO. Tiempo total: {tiempo:.2f} segundos")
    return tiempo

async def simular_peticion(session, demora, nombre):
    # Esta función no bloquea, cede el control
    await asyncio.sleep(demora)
    # print(f"      ✅ {nombre} recibido") # Descomentar si quieres ver detalles

# --- 3. EL RING DE PELEA (Main) ---
if __name__ == "__main__":
    print("🥊 --- INICIANDO COMPARATIVA DE VELOCIDAD ---")
    
    # Round 1: Síncrono
    tiempo_sync = ejecutar_dashboard_sincrono()
    
    # Pausa dramática
    time.sleep(1)
    
    # Round 2: Asíncrono
    tiempo_async = asyncio.run(ejecutar_dashboard_asincrono())
    
    # --- RESULTADOS FINALES ---
    print("\n" + "="*40)
    print("🏆 TABLA FINAL DE RESULTADOS")
    print("="*40)
    print(f"🐢 Síncrono (Secuencial): {tiempo_sync:.2f} s")
    print(f"🚀 Asíncrono (Paralelo):   {tiempo_async:.2f} s")
    print("-" * 40)
    
    mejora = tiempo_sync / tiempo_async
    print(f"💡 CONCLUSIÓN: El código asíncrono es {mejora:.1f}x veces más rápido.")
    print("="*40)