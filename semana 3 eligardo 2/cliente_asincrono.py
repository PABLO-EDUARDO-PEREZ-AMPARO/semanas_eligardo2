import aiohttp
import asyncio
import time
import os
from aiohttp import ClientTimeout

class ErrorValidacion(Exception): pass
class ErrorNoEncontrado(Exception): pass
class ErrorServidor(Exception): pass

# Configuración
BASE_URL = "http://localhost:9999"
TIMEOUT_SEG = 2  # Máximo 2 segundos de espera

async def obtener_producto(session, prod_id):
    url = f"{BASE_URL}/productos/{prod_id}"
    print(f"⏳ Pidiendo ID {prod_id}...")

    try:
        # Configuración estricta del Timeout
        timeout_config = aiohttp.ClientTimeout(total=TIMEOUT_SEG, connect=1)
        
        async with session.get(url, timeout=timeout_config) as response:
            if response.status >= 500:
                print(f"❌ ID {prod_id}: Error servidor ({response.status})")
                return
            
            if response.status == 404:
                print(f"⚠️ ID {prod_id}: No encontrado")
                return

            data = await response.json()
            print(f"✅ ID {prod_id}: {data['nombre']} (${data['precio']})")

    except asyncio.TimeoutError:
        print(f"⏰ ID {prod_id}: ¡Timeout! (Se canceló por tardar más de {TIMEOUT_SEG}s)")
    except Exception as e:
        print(f"💀 ID {prod_id}: Error: {e}")

async def main():
    print("--- 🚀 INICIANDO DESCARGA ASÍNCRONA ---")
    start_time = time.perf_counter()

    ids_a_descargar = [1, 500, 2, 999, 3]

    # Creamos la sesión una sola vez
    async with aiohttp.ClientSession() as session:
        # Creamos la lista de tareas
        tareas = []
        for id_prod in ids_a_descargar:
            tarea = obtener_producto(session, id_prod)
            tareas.append(tarea)
        
        # Ejecutamos todas las tareas a la vez
        await asyncio.gather(*tareas)

    total_tiempo = time.perf_counter() - start_time
    print("-" * 30)
    print(f"🏁 Todo terminado en {total_tiempo:.2f} segundos.")

if __name__ == "__main__":
    # --- BORRAMOS EL PARCHE DE WINDOWS ---
    # En Python 3.14 ya no hace falta y causa conflictos.
    asyncio.run(main())