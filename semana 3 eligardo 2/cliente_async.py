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
    
    # Invariante: Session siempre se pasa como argumento, no se crea dentro
    async def listar_productos(self, session: aiohttp.ClientSession):
        print("   🔍 Listando productos...")
        try:
            async with session.get(f"{BASE_URL}/productos", timeout=2) as resp:
                if resp.status == 200:
                    return await resp.json()
                raise ErrorServidor(f"Error {resp.status}")
        except Exception as e:
            raise ErrorServidor(f"Fallo al listar: {e}")

    async def obtener_producto(self, session: aiohttp.ClientSession, pid):
        # print(f"   🔍 Buscando ID {pid}...") 
        try:
            async with session.get(f"{BASE_URL}/productos/{pid}", timeout=2) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status >= 500:
                    raise ErrorServidor(f"Server Error {resp.status}")
                return None
        except asyncio.TimeoutError:
            raise ErrorServidor(f"Timeout ID {pid}")

    async def crear_producto(self, session: aiohttp.ClientSession, datos):
        # print(f"   💾 Creando {datos['nombre']}...")
        try:
            async with session.post(f"{BASE_URL}/productos", json=datos, timeout=2) as resp:
                if resp.status == 201:
                    return await resp.json()
                raise ErrorServidor(f"Error al crear: {resp.status}")
        except Exception as e:
            raise ErrorServidor(str(e))

    # --- SIMULACIONES PARA EL DASHBOARD ---
    async def obtener_categorias(self, session):
        await asyncio.sleep(0.5) # Simula red
        return ["Tecnología", "Hogar", "Ropa"]

    async def obtener_perfil(self, session):
        await asyncio.sleep(0.3) # Simula red
        return {"usuario": "Eligardo", "nivel": "Oro"}

# --- FUNCIÓN 1: DASHBOARD (Carga Paralela) ---
async def cargar_dashboard():
    print("\n📊 --- CARGANDO DASHBOARD (GATHER) ---")
    cliente = ClienteEcoMarketAsync()
    
    # Invariante: Context Manager para la sesión
    async with aiohttp.ClientSession() as session:
        inicio = time.perf_counter()
        
        # Lanzamos 3 tareas a la vez
        t1 = cliente.listar_productos(session)
        t2 = cliente.obtener_categorias(session)
        t3 = cliente.obtener_perfil(session)
        
        # Esperamos todas (return_exceptions=True evita que una falla cancele todo)
        res_prods, res_cats, res_perf = await asyncio.gather(t1, t2, t3, return_exceptions=True)
        
        fin = time.perf_counter()
        
        print(f"✅ Dashboard cargado en {fin - inicio:.2f} segundos")
        print(f"   📦 Productos: {res_prods}")
        print(f"   📂 Categorías: {res_cats}")
        print(f"   👤 Perfil: {res_perf}")

# --- FUNCIÓN 2: CREACIÓN MASIVA (Semáforos) ---
async def crear_multiples_productos():
    print("\n🏭 --- INICIANDO CREACIÓN MASIVA (SEMÁFORO) ---")
    cliente = ClienteEcoMarketAsync()
    lista_productos = [{"nombre": f"Prod-{i}", "precio": i*10} for i in range(10)]
    
    # SEMÁFORO: Solo 5 obreros trabajando a la vez
    sem = asyncio.Semaphore(5)
    
    async with aiohttp.ClientSession() as session:
        
        async def trabajador(prod):
            async with sem: # Aquí entra al cuarto limitado
                print(f"   👷 Procesando {prod['nombre']}...")
                # Simulamos un poquito de retardo para ver el efecto
                await asyncio.sleep(0.5) 
                return await cliente.crear_producto(session, prod)

        start = time.perf_counter()
        tareas = [trabajador(p) for p in lista_productos]
        
        # Ejecutamos
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        end = time.perf_counter()

        exitos = [r for r in resultados if not isinstance(r, Exception)]
        errores = [r for r in resultados if isinstance(r, Exception)]
        
        print(f"🏁 Terminado en {end - start:.2f}s")
        print(f"   ✅ Creados: {len(exitos)}")
        print(f"   ❌ Fallidos: {len(errores)}")

if __name__ == "__main__":
    # --- CÓDIGO LIMPIO SIN EL PARCHE DE WINDOWS ---
    try:
        # Ejecutamos las dos pruebas principales
        asyncio.run(cargar_dashboard())
        asyncio.run(crear_multiples_productos())
    except KeyboardInterrupt:
        print("\n👋 Ejecución cancelada por el usuario.")
    except Exception as e:
        print(f"\n💀 Error inesperado: {e}")