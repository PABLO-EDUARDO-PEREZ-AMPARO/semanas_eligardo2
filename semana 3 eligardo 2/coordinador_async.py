import asyncio
import aiohttp
import time

# --- EXCEPCIONES PARA SIMULACIÓN ---
class ErrorCritico(Exception): pass

class CoordinadorAsync:
    """
    Módulo encargado de orquestar peticiones asíncronas con 
    estrategias de resiliencia y prioridad.
    """

    # =================================================================
    # ESTRATEGIA 1: TIMEOUT GRANULAR (Protección Individual)
    # =================================================================
    async def peticion_con_timeout(self, nombre, tiempo_simulado, limite_tiempo):
        """
        Envuelve una tarea. Si tarda más del límite, la corta.
        """
        try:
            print(f"   🔵 [{nombre}] Iniciando (Tardará {tiempo_simulado}s, Límite {limite_tiempo}s)...")
            
            # Simulamos el trabajo real
            async def trabajo_real():
                await asyncio.sleep(tiempo_simulado)
                return "✅ Éxito"

            # Aquí aplicamos el timeout
            resultado = await asyncio.wait_for(trabajo_real(), timeout=limite_tiempo)
            print(f"   ✅ [{nombre}] Terminó a tiempo.")
            return resultado
            
        except asyncio.TimeoutError:
            print(f"   ❌ [{nombre}] TIMEOUT: Se canceló por tardar demasiado.")
            return None
        except Exception as e:
            print(f"   ⚠️ [{nombre}] Error: {e}")
            return None

    # =================================================================
    # ESTRATEGIA 2: CANCELACIÓN EN CASCADA (Fail-Fast)
    # =================================================================
    async def ejecutar_cancelacion_grupo(self):
        print("\n🛡️ --- ESTRATEGIA 2: CANCELACIÓN EN GRUPO (Fail-Fast) ---")
        print("   Escenario: El Login falla (401), así que cancelamos descargas innecesarias.")
        
        async def login_fallido():
            await asyncio.sleep(0.5)
            print("   ⛔ [Login] Falló: Credenciales inválidas.")
            raise ErrorCritico("401 Unauthorized")

        async def descarga_pesada(id):
            try:
                print(f"   ⏳ [Descarga {id}] Iniciando...")
                await asyncio.sleep(5) # Tarea larga
                print(f"   ✅ [Descarga {id}] Terminada.")
            except asyncio.CancelledError:
                print(f"   🛑 [Descarga {id}] FUE CANCELADA por el coordinador.")
                raise # Importante relanzar para que asyncio sepa que se canceló

        # Creamos las tareas manualmente
        t_login = asyncio.create_task(login_fallido())
        t_datos1 = asyncio.create_task(descarga_pesada(1))
        t_datos2 = asyncio.create_task(descarga_pesada(2))
        
        tareas_secundarias = [t_datos1, t_datos2]

        try:
            # Esperamos la crítica (Login)
            await t_login
        except ErrorCritico:
            print("   ⚠️ Detectado fallo crítico. Cancelando tareas secundarias...")
            for t in tareas_secundarias:
                t.cancel()
            
            # Esperamos a que terminen de cancelarse
            await asyncio.gather(*tareas_secundarias, return_exceptions=True)

    # =================================================================
    # ESTRATEGIA 3: CARGA CON PRIORIDAD (Wait)
    # =================================================================
    async def ejecutar_carga_prioritaria(self):
        print("\n⚡ --- ESTRATEGIA 3: CARGA CON PRIORIDAD ---")
        print("   Escenario: Mostrar datos críticos YA, cargar secundarios DESPUÉS.")
        
        start = time.perf_counter()

        # Tareas
        # 1. Perfil (Rápido, Crítico)
        t_perfil = asyncio.create_task(self.peticion_con_timeout("Perfil", 1.0, 2.0))
        # 2. Productos (Medio, Crítico)
        t_prods = asyncio.create_task(self.peticion_con_timeout("Productos", 2.0, 3.0))
        # 3. Ads (Muy Lento, Secundario)
        t_ads = asyncio.create_task(self.peticion_con_timeout("Publicidad", 4.0, 1.0)) # ¡Timeout corto intencional!

        criticas = [t_perfil, t_prods]
        secundarias = [t_ads] # Publicidad tiene timeout de 1s, fallará.

        print("   ⏳ Esperando tareas CRÍTICAS...")
        await asyncio.wait(criticas, return_when=asyncio.ALL_COMPLETED)
        
        tiempo = time.perf_counter() - start
        print(f"   ✨ ¡DASHBOARD PARCIAL VISIBLE! (Tiempo: {tiempo:.2f}s)")
        print("   (El usuario ya puede usar la app mientras lo demás carga...)")

        print("   ⏳ Procesando tareas SECUNDARIAS...")
        await asyncio.wait(secundarias)
        print("   🏁 Todo finalizado.")

# --- EJECUCIÓN DEL COORDINADOR ---
async def main():
    coordinador = CoordinadorAsync()
    
    # 1. Demostración de Timeout Individual
    print("\n⏱️ --- ESTRATEGIA 1: TIMEOUT INDIVIDUAL ---")
    await coordinador.peticion_con_timeout("Prueba_Lenta", 3.0, 1.0) # Tardará 3, Límite 1 -> FALLA

    # 2. Demostración de Cancelación
    await coordinador.ejecutar_cancelacion_grupo()

    # 3. Demostración de Prioridad
    await coordinador.ejecutar_carga_prioritaria()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass