# examne eligardo

import asyncio
import aiohttp

Ninguno = None
Falso = False  
Verdadero = True



# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
BASE_URL        = "http://ecomarket.local/api/v1"
TOKEN           = "eyJ0eXAiO..."          # token proporcionado en el examen
INTERVALO_BASE  = 5                       # segundos entre consultas
INTERVALO_MAX   = 60                      # máximo de backoff
TIMEOUT         = 10                      # segundos de timeout por petición

# ─── INTERFAZ OBSERVADOR ──────────────────────────────────────────────────────
class abstracta :
     

# ─── OBSERVABLE ───────────────────────────────────────────────────────────────
    class MonitorInventario:
        def __init__(self):
            self._observadores = []
            self._ultimo_etag  = Ninguno
            self._ultimo_estado= Ninguno
            self._ejecutando   = Falso
            self._intervalo    = INTERVALO_BASE

    def suscribir(self, obs): 
        if obs not in self._observadores:
            self._observadores.append(obs)
   
    def _notificar(self, inventario):
        for obs in self._observadores:
            try:
                obs.actualizar(inventario)
            except Exception as e:
                print(f"⚠️ Error en observador {type(obs).__name__}: {e}")

      

    async def _consultar_inventario(self ):
        headers = {"Authorization": f"Bearer {TOKEN}"
                   ,"accept": "application"}
        if self._ultimo_etag:
            headers["If-None-Match"] = self._ultimo_etag
            
        
       

    async def iniciar(self):
        self._ejecutando = Verdadero
        async with aiohttp.ClientSession() as self._session:
         while self._ejecutando:
            datos = await self._consultar_inventario(session=self._session)
            if datos and datos != self._ultimo_estado:
                self._ultimo_estado = datos
                self._notificar(datos)
                self._intervalo = INTERVALO_BASE  

                await asyncio.sleep(self._intervalo)

           