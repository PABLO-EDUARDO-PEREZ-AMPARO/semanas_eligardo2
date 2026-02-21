import asyncio
import aiohttp
import time
from aiohttp import ClientTimeout

# --- CONFIGURACIÓN ---
BASE_URL = "http://localhost:9999"

# --- EXCEPCIONES ---
class ErrorEcoMarket(Exception): pass
class ErrorValidacion(ErrorEcoMarket): pass
class ErrorServidor(ErrorEcoMarket): pass

class ClienteEcoMarketAsync:
    
    # 1. LISTAR (GET)
    async def listar_productos(self, session: aiohttp.ClientSession):
        try:
            async with session.get(f"{BASE_URL}/productos", timeout=2) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise ErrorServidor(f"Error {resp.status}")
        except Exception as e:
            raise ErrorServidor(f"Fallo al listar: {e}")

    # 2. OBTENER UNO (GET)
    async def obtener_producto(self, session: aiohttp.ClientSession, pid):
        try:
            async with session.get(f"{BASE_URL}/productos/{pid}", timeout=2) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    return None
                raise ErrorServidor(f"Error {resp.status}")
        except asyncio.TimeoutError:
            raise ErrorServidor(f"Timeout ID {pid}")

    # 3. CREAR (POST)
    async def crear_producto(self, session: aiohttp.ClientSession, datos):
        try:
            async with session.post(f"{BASE_URL}/productos", json=datos, timeout=2) as resp:
                if resp.status == 201:
                    return await resp.json()
                raise ErrorServidor(f"Error al crear: {resp.status}")
        except Exception as e:
            raise ErrorServidor(str(e))

    # 4. ACTUALIZAR TOTAL (PUT) - ¡NUEVO!
    async def actualizar_producto_total(self, session: aiohttp.ClientSession, pid, datos):
        try:
            async with session.put(f"{BASE_URL}/productos/{pid}", json=datos, timeout=2) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise ErrorServidor(f"Error PUT: {resp.status}")
        except Exception as e:
            raise ErrorServidor(str(e))

    # 5. ACTUALIZAR PARCIAL (PATCH) - ¡NUEVO!
    async def actualizar_producto_parcial(self, session: aiohttp.ClientSession, pid, campos):
        try:
            async with session.patch(f"{BASE_URL}/productos/{pid}", json=campos, timeout=2) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise ErrorServidor(f"Error PATCH: {resp.status}")
        except Exception as e:
            raise ErrorServidor(str(e))

    # 6. ELIMINAR (DELETE) - ¡NUEVO!
    async def eliminar_producto(self, session: aiohttp.ClientSession, pid):
        try:
            async with session.delete(f"{BASE_URL}/productos/{pid}", timeout=2) as resp:
                if resp.status in [200, 204]:
                    return True
                raise ErrorServidor(f"Error DELETE: {resp.status}")
        except Exception as e:
            raise ErrorServidor(str(e))

    # --- SIMULACIONES PARA EL DASHBOARD ---
    async def obtener_categorias(self, session):
        # Simulamos latencia de red de 0.5s
        await asyncio.sleep(0.5) 
        return ["Tecnología", "Hogar", "Ropa"]

    async def obtener_perfil(self, session):
        # Simulamos latencia de red de 0.3s
        await asyncio.sleep(0.3) 
        return {"usuario": "Eligardo", "nivel": "Oro"}

# --- FUNCIÓN: DASHBOARD (CARGA PARALELA) ---
async def cargar_dashboard():
    print("\n📊 --- CARGANDO DASHBOARD (SÍNCRONO VS ASÍNCRONO) ---")
    cliente = ClienteEcoMarketAsync()
    
    async with aiohttp.ClientSession() as session:
        inicio = time.perf_counter()
        
        # Lanzamos 3 tareas a la vez
        t1 = cliente.listar_productos(session)
        t2 = cliente.obtener_categorias(session)
        t3 = cliente.obtener_perfil(session)
        
        # Gather espera a que TODAS terminen, pero se ejecutan a la vez
        res_prods, res_cats, res_perf = await asyncio.gather(t1, t2, t3, return_exceptions=True)
        
        fin = time.perf_counter()
        tiempo_total = fin - inicio
        
        print(f"✅ Dashboard ASÍNCRONO cargado en: {tiempo_total:.2f} segundos")
        return tiempo_total

# --- FUNCIÓN: CREACIÓN MASIVA (SEMÁFORO) ---
async def crear_multiples_productos():
    print("\n🏭 --- INICIANDO CREACIÓN MASIVA ---")
    cliente = ClienteEcoMarketAsync()
    lista_productos = [{"nombre": f"Prod-{i}", "precio": i*10} for i in range(10)]
    sem = asyncio.Semaphore(5)
    
    async with aiohttp.ClientSession() as session:
        async def trabajador(prod):
            async with sem:
                # await asyncio.sleep(0.1) # Pequeña pausa para ver el efecto
                return await cliente.crear_producto(session, prod)

        start = time.perf_counter()
        tareas = [trabajador(p) for p in lista_productos]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        end = time.perf_counter()

        print(f"🏁 Creación Masiva terminada en: {end - start:.2f} segundos")

if __name__ == "__main__":
    try:
        asyncio.run(cargar_dashboard())
        asyncio.run(crear_multiples_productos())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")