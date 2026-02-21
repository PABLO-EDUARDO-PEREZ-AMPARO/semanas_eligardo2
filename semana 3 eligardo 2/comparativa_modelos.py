import time
import threading
import requests
import asyncio
import aiohttp
import os

# --- CAMBIO 1: Usamos la IP directa para evitar error de "getaddrinfo" ---
BASE_URL = "http://127.0.0.1:9999/productos" # Antes localhost
IDS = [1, 500, 2, 999, 3]

# ==========================================
# 🐢 MODELO 1: SÍNCRONO (El Lento)
# ==========================================
def peticion_sincrona(id_prod):
    # print(f"   ⏳ Pidiendo ID {id_prod}...", flush=True) <-- Comentado para limpiar output
    try:
        resp = requests.get(f"{BASE_URL}/{id_prod}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ ID {id_prod}: {data['nombre']} (${data['precio']})")
        elif resp.status_code >= 500:
            print(f"   ❌ ID {id_prod}: Error servidor ({resp.status_code})")
        else:
            print(f"   ⚠️ ID {id_prod}: Estado {resp.status_code}")
    except Exception as e:
        print(f"   💀 ID {id_prod}: Error conexión")

def correr_sincrono():
    print("\n" + "="*40)
    print("🐢 1. MODELO SÍNCRONO (Uno por uno)")
    print("="*40)
  
    start = time.time()
    for id_prod in IDS:
        print(f"   ⏳ Enviando ID {id_prod}...")
        peticion_sincrona(id_prod)
    return time.time() - start

# ==========================================
# 🐇 MODELO 2: HILOS (El Desordenado)
# ==========================================
def correr_hilos():
    print("\n" + "="*40)
    print("🐇 2. MODELO HILOS (Threading)")
    print("="*40)
    start = time.time()
    hilos = []
    
    for id_prod in IDS:
        hilo = threading.Thread(target=peticion_sincrona, args=(id_prod,))
        hilos.append(hilo)
        hilo.start()
    
    for hilo in hilos:
        hilo.join()
        
    return time.time() - start

# ==========================================
# 🚀 MODELO 3: ASÍNCRONO (El Tuyo - Optimizado)
# ==========================================
async def peticion_asincrona(session, prod_id):
    # print(f"   ⏳ Pidiendo ID {prod_id}...")
    try:
        # Timeout de 2 segundos
        timeout = aiohttp.ClientTimeout(total=2) 
        async with session.get(f"{BASE_URL}/{prod_id}", timeout=timeout) as response:
            if response.status >= 500:
                print(f"   ❌ ID {prod_id}: Error servidor ({response.status})")
                return
            data = await response.json()
            print(f"   ✅ ID {prod_id}: {data['nombre']} (${data['precio']})")
    except asyncio.TimeoutError:
        print(f"   ⏰ ID {prod_id}: ¡Timeout! (Cancelado por lento)")
    except Exception as e:
        print(f"   💀 ID {prod_id}: Error {e}")

async def main_async():
    print("\n" + "="*40)
    print("🚀 3. MODELO ASÍNCRONO (Inteligente)")
    print("="*40)
    start = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        # Creamos todas las tareas
        tareas = [peticion_asincrona(session, id) for id in IDS]
        print(f"   ⚡ Lanzando {len(IDS)} peticiones a la vez...")
        # Ejecutamos
        await asyncio.gather(*tareas)
    return time.perf_counter() - start

# ==========================================
# 🏁 ORQUESTADOR PRINCIPAL
# ==========================================
if __name__ == "__main__":
    # --- CAMBIO 2: Borramos el parche de Windows que daba error ---
    
    print("--- INICIANDO COMPARATIVA VISUAL ---")
    
    # 1. Correr Síncrono
    t1 = correr_sincrono()
    
    # 2. Correr Hilos
    t2 = correr_hilos()
    
    # 3. Correr Asíncrono
    t3 = asyncio.run(main_async())

    print("\n" + "="*40)
    print("📊 TABLA FINAL DE RESULTADOS")
    print("="*40)
    print(f"1. 🐢 Síncrono:  {t1:.2f} s")
    print(f"2. 🐇 Hilos:     {t2:.2f} s")
    print(f"3. 🚀 Asíncrono: {t3:.2f} s")
    print("="*40)