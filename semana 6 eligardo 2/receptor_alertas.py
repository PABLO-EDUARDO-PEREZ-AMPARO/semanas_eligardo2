"""
Cliente SSE para EcoMarket - Ruta A
Autor: [Tu Nombre]

--- TRADE-OFFS DE DISEÑO ---
ETAPA 1 (Conexión): 
Trade-off: Usamos un timeout largo (30s) en httpx y leemos como stream continuo. 
Desventaja: Mantiene un hilo/conexión de red ocupado indefinidamente.
Ventaja: Evita el overhead (costo de procesamiento) de abrir y cerrar conexiones a cada rato como en el Polling.

ETAPA 2 (Parseo con Buffer):
Trade-off: Usamos un Diccionario en memoria como 'buffer' para acumular las líneas.
Desventaja: Consume ligeramente más memoria RAM que ir concatenando un solo String crudo.
Ventaja: Garantiza precisión absoluta al separar el 'id', 'event' y 'data', evitando que un mensaje malformado rompa la lógica.

ETAPA 3 (Reconexión y Last-Event-ID):
Trade-off: Implementamos un 'Backoff Exponencial' (3s, 6s, 12s...) en lugar de reconectar inmediatamente (0s).
Desventaja: El cliente tarda un poco más en recuperar la conexión si el fallo fue solo un micro-corte.
Ventaja: Protege al servidor de EcoMarket de sufrir un ataque DDoS accidental si miles de clientes intentan reconectarse exactamente en el mismo milisegundo.
"""



"""
ENTREGABLE NUMERO 3

RECEPTOR ALERTAS ECOMARKET — Decisiones de arquitectura (cliente)

ESCENARIO A (10k usuarios, precios cambian poco):
- SSE elegido sobre Polling. por que mantener 1 conexión TCP inactiva gasta muy poca RAM en el 
  dispositivo. Por el contrario, hacer Polling despertaría la antena del celular 
  constantemente para enviar peticiones HTTP inútiles, destrozando la batería del cliente.

ESCENARIO B (Servidor Legacy, actualizaciones cada 1s):
- Polling clásico es obligatorio. al no soportar streaming, forzar SSE causaría errores 
  de parseo en el cliente al no recibir el formato estándar (\n\n). El alto costo de red 
  se asume, mitigando el impacto visual actualizando solo nodos específicos.

ESCENARIO C (Red 3G inestable en movimiento):
- SSE elegido sobre el Polling. Aprovecha la reconexión automática del navegador. 
  El uso nativo del header Last-Event-ID garantiza la recuperación de alertas perdidas 
  durante los micro-cortes, evitando programar lógica manual compleja de reintentos.

ESCENARIO D (Alertas continuas + Filtros dinámicos):
- Modelo híbrido (SSE para lectura + peticiones POST para escritura) elegido sobre WebSockets. 
  Aunque abre conexiones extra al filtrar, simplifica drásticamente la arquitectura del 
  frontend al no tener que gestionar a mano la reconexión bidireccional ni el estado del socket.
"""

import asyncio
import httpx

async def receptor_alertas():
    corriendo = True
    ultimo_id = None
    retry_ms = 3000
    intentos = 0
    max_intentos = 5

    while corriendo and intentos < max_intentos:
        url = "https://sse.dev/test"
        
        headers = {"Accept": "text/event-stream"}
        if ultimo_id:
            headers["Last-Event-ID"] = ultimo_id
            # Imprimimos los headers para que salgan en el log de validación
            print(f"🔄 Reconectando... Headers enviados: {headers}")

        timeout = httpx.Timeout(30.0)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream('GET', url, headers=headers) as response:
                    
                    if response.status_code == 204:
                        print("🛑 [204 No Content] Fin de transmisión.")
                        corriendo = False
                        break
                    
                    print("✅ Conexión inicial establecida. Escuchando eventos...\n")
                    intentos = 0
                    buffer = {"id": None, "event": None, "data": ""}

                    async for linea in response.aiter_lines():
                        if not corriendo: break
                        if linea.startswith(":"): continue

                        if linea == "":
                            if buffer["event"] or buffer["data"]:
                                print(f"📩 Procesado: {buffer['event']} -> {buffer['data']}")
                                if buffer["id"]:
                                    ultimo_id = buffer["id"]
                            buffer = {"id": None, "event": None, "data": ""}
                            continue

                        if ":" in linea:
                            clave, valor = linea.split(":", 1)
                            clave, valor = clave.strip(), valor.strip()
                            
                            if clave == "id": buffer["id"] = valor
                            elif clave == "event": buffer["event"] = valor
                            elif clave == "data": buffer["data"] += valor
                            elif clave == "retry": retry_ms = int(valor)

        except Exception as e:
            intentos += 1
            if intentos < max_intentos:
                espera = (retry_ms / 1000) * (2 ** (intentos - 1))
                print(f"❌ Red caída ({e}). Reintentando en {espera}s... (Intento {intentos}/{max_intentos})")
                await asyncio.sleep(espera)
            else:
                print("💥 Max intentos alcanzados. Fin.")

if __name__ == "__main__":
    asyncio.run(receptor_alertas())