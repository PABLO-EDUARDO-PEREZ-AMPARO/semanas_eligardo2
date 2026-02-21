import asyncio
import aiohttp
import time

# --- EXCEPCIONES PERSONALIZADAS ---
class ErrorAuth(Exception): pass

class ClienteAvanzado:
    
    # ==========================================
    # 1. WRAPPER DE SEGURIDAD (Timeout)
    # ==========================================
    async def peticion_segura(self, corutina, timeout_sec, nombre):
        """
        Envuelve una tarea con un temporizador.
        Si explota o tarda mucho, retorna None para no romper el flujo.
        """
        try:
            return await asyncio.wait_for(corutina, timeout=timeout_sec)
        except asyncio.TimeoutError:
            print(f"   ⏰ [TIMEOUT] {nombre} tardó demasiado (> {timeout_sec}s). Cancelada.")
            return None
        except Exception as e:
            print(f"   ❌ [ERROR] {nombre}: {e}")
            return None

    # --- SIMULACIÓN DE PETICIONES (Mocks) ---
    # Usamos sleep para garantizar que veas los efectos de tiempo
    async def get_perfil(self, fail=False):
        print("      👤 Buscando Perfil...")
        await asyncio.sleep(1) # Rápido
        if fail: raise ErrorAuth("Usuario no logueado")
        return "Datos-Perfil"

    async def get_productos(self, delay=2):
        print(f"      📦 Buscando Productos (tarda {delay}s)...")
        await asyncio.sleep(delay) 
        return ["TV", "Laptop", "Mouse"]

    async def get_ads(self):
        print("      📢 Buscando Publicidad (Lento)...")
        await asyncio.sleep(4) # Muy lento
        return "Compra 2x1!"

    # ==========================================
    # 2. CANCELACIÓN EN CASCADA
    # ==========================================
    async def demo_cancelacion(self):
        print("\n💀 --- ESCENARIO 1: CANCELACIÓN POR ERROR CRÍTICO ---")
        async with aiohttp.ClientSession() as session:
            # Lanzamos las tareas, pero guardamos la referencia 't'
            t_perfil = asyncio.create_task(self.get_perfil(fail=True)) # Fallará
            t_prods = asyncio.create_task(self.get_productos())
            t_ads = asyncio.create_task(self.get_ads())

            try:
                # El perfil es obligatorio, lo esperamos primero
                await t_perfil
            except ErrorAuth:
                print("   ⛔ ¡ERROR CRÍTICO (401)! Deteniendo descargas innecesarias...")
                
                # Cancelamos las otras tareas manualmente
                t_prods.cancel()
                t_ads.cancel()
                
                # Esperamos a que se limpien (boilerplate necesario)
                await asyncio.gather(t_prods, t_ads, return_exceptions=True)
                print("   ✅ Tareas secundarias canceladas exitosamente.")

    # ==========================================
    # 3. CARGA PRIORITARIA (WAIT)
    # ==========================================
    async def demo_prioridad(self):
        print("\n⚡ --- ESCENARIO 2: CARGA INTELIGENTE (PRIORIDAD) ---")
        async with aiohttp.ClientSession() as session:
            
            # Definimos tareas con nuestros Timeouts Seguros
            # Perfil: Timeout 2s
            task_perfil = asyncio.create_task(
                self.peticion_segura(self.get_perfil(), 2, "Perfil"))
            
            # Productos: Tarda 2s, Timeout 3s (OK)
            task_prods = asyncio.create_task(
                self.peticion_segura(self.get_productos(delay=2), 3, "Productos"))
            
            # Ads: Tarda 4s, Timeout 1s (FALLARÁ POR TIMEOUT INTENCIONALMENTE)
            task_ads = asyncio.create_task(
                self.peticion_segura(self.get_ads(), 1, "Publicidad"))

            # Clasificamos
            criticas = [task_perfil, task_prods]
            secundarias = [task_ads]

            print("   ⏳ Esperando contenido CRÍTICO (Perfil + Productos)...")
            start = time.perf_counter()
            
            # wait: Espera solo a las críticas
            await asyncio.wait(criticas, return_when=asyncio.ALL_COMPLETED)
            
            mid = time.perf_counter()
            print(f"   ✨ ¡DASHBOARD LISTO! (En {(mid-start):.2f}s) - Usuario ya puede interactuar.")

            print("   ⏳ Cargando secundarias en segundo plano...")
            await asyncio.wait(secundarias)
            
            end = time.perf_counter()
            print(f"   🏁 Todo terminado en {(end-start):.2f}s")

# --- MAIN ---
if __name__ == "__main__":
    cliente = ClienteAvanzado()
    try:
        asyncio.run(cliente.demo_cancelacion())
        # Pequeña pausa para leer
        time.sleep(1)
        asyncio.run(cliente.demo_prioridad())
    except KeyboardInterrupt:
        pass