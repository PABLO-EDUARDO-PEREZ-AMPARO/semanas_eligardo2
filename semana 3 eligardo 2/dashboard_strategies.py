import asyncio
import random

# Mock de peticiones
async def fetch(name, delay, fail=False):
    await asyncio.sleep(delay)
    if fail: raise Exception(f"Error en {name}")
    return f"Datos de {name}"

async def demo_estrategias():
    tasks = {
        fetch("Categorías", 0.1),
        fetch("Productos", 0.2),
        fetch("Perfil", 0.5),
        fetch("Notificaciones", 2.0, fail=True) # Simulamos fallo/lento
    }

    # --- 1. GATHER (El "Todo o Nada") ---
    # Ventaja: Simple. Desventaja: El usuario espera al más lento.
    res = await asyncio.gather(*tasks, return_exceptions=True)

    # --- 2. WAIT FIRST_COMPLETED (El "Sprint") ---
    # Ventaja: Reacción inmediata al primer dato. Desventaja: Deja tareas huérfanas.
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    primer_dato = await list(done)[0]

    # --- 3. AS_COMPLETED (El "Streaming") ---
    # Ventaja: Ideal para UI. Vas "pintando" conforme llegan.
    for coro in asyncio.as_completed(tasks):
        try:
            resultado = await coro
            print(f"Update UI: {resultado}")
        except Exception as e: print(f"UI Error: {e}")

    # --- 4. WAIT FIRST_EXCEPTION (El "Seguro") ---
    # Ventaja: Si algo crítico falla, abortamos el resto.
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)