import asyncio
import httpx

async def cliente_ecomarket_prod():
    corriendo = True
    ultimo_id = None
    retry_ms = 5000

    while corriendo:
        url = "https://api.ecomarket.local/alertas"
        headers = {"Accept": "text/event-stream"}
        
        if ultimo_id:
            headers["Last-Event-ID"] = str(ultimo_id)

        timeout = httpx.Timeout(connect=10.0, read=60.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream('GET', url, headers=headers) as response:
                    
                    if response.status_code == 204:
                        corriendo = False
                        break

                    buffer = {"id": None, "event": None, "data": ""}

                    async for linea in response.aiter_lines():
                        if not corriendo: 
                            break

                        if linea.startswith(":"):
                            continue

                        if linea == "":
                            if buffer["event"] or buffer["data"]:
                                print(f"📩 Evento procesado: {buffer['event']} | Datos: {buffer['data']}")
                                
                    
                                if buffer["id"] is not None:
                                    ultimo_id = buffer["id"]
                                
                            buffer = {"id": None, "event": None, "data": ""}
                            continue

                        if ":" in linea:
                            clave, valor = linea.split(":", 1)
                            clave = clave.strip()
                            valor = valor.strip()

                            if clave == "id":
                                buffer["id"] = valor
                            
                                
                            elif clave == "event":
                                buffer["event"] = valor
                                
                            elif clave == "data":
                                
                                buffer["data"] += valor + "\n" 
                                
                            elif clave == "retry":
                                retry_ms = int(valor)

        except Exception as e:
            
            print(f"⚠️ Caída de red ({e}). Reintentando en {retry_ms / 1000}s...")
            await asyncio.sleep(retry_ms / 1000)

if __name__ == "__main__":
    
    asyncio.run(cliente_ecomarket_prod())