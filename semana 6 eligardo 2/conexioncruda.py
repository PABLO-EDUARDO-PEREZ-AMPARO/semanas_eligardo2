import asyncio
import httpx

async def cliente_sse_indestructible():
    # --- VARIABLES EXTERNAS (Tu memoria a largo plazo) ---
    corriendo = True           # Bandera de apagado limpio
    ultimo_id = None           # Aquí guardamos el ID seguro
    retry_ms = 3000            # Tiempo de espera por defecto (3 seg)
    intentos = 0
    max_intentos = 5

    while corriendo and intentos < max_intentos:
        url = "https://sse.dev/test"
        
        # 1. Preparamos los Headers. ¡Si tenemos memoria, la mandamos!
        headers = {"Accept": "text/event-stream"}
        if ultimo_id:
            headers["Last-Event-ID"] = ultimo_id
            print(f"🔄 Reconectando... Pidiendo desde el evento ID: {ultimo_id}")

        timeout = httpx.Timeout(30.0)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream('GET', url, headers=headers) as response:
                    
                    # 2. Si el servidor dice "Ya no hay más" (204), nos apagamos limpios
                    if response.status_code == 204:
                        print("🛑 [204 No Content] El servidor cerró la transmisión. Apagando...")
                        corriendo = False
                        break
                    
                    print("✅ Conexión establecida. Escuchando...")
                    intentos = 0  # Si conectamos bien, reseteamos los errores
                    
                    # El buffer temporal (se borra a cada rato)
                    buffer = {"id": None, "event": None, "data": ""}

                    async for linea in response.aiter_lines():
                        if not corriendo: 
                            break  # Freno de emergencia

                        if linea.startswith(":"):
                            continue  # Ignoramos el ping

                        # 3. ¡MENSAJE COMPLETO!
                        if linea == "":
                            if buffer["event"] or buffer["data"]:
                                print(f"📩 Procesado: {buffer['event']} -> {buffer['data']}")
                                
                                # ¡TU LÓGICA AQUÍ! Solo actualizamos la memoria si el mensaje está completo
                                if buffer["id"]:
                                    ultimo_id = buffer["id"]
                            
                            # Vaciamos el buffer temporal, pero ultimo_id está a salvo afuera
                            buffer = {"id": None, "event": None, "data": ""}
                            continue

                        # 4. Leer líneas individuales
                        if ":" in linea:
                            clave, valor = linea.split(":", 1)
                            clave, valor = clave.strip(), valor.strip()
                            
                            if clave == "id":
                                buffer["id"] = valor
                            elif clave == "event":
                                buffer["event"] = valor
                            elif clave == "data":
                                buffer["data"] += valor
                            elif clave == "retry":
                                retry_ms = int(valor) # El servidor puede cambiar el tiempo de espera

        except Exception as e:
            intentos += 1
            if intentos < max_intentos:
                # Calculamos el Backoff Exponencial (esperar 3s, luego 6s, 12s, 24s...)
                espera = (retry_ms / 1000) * (2 ** (intentos - 1))
                print(f"❌ Red caída: {e}. Reintentando en {espera}s... (Intento {intentos}/{max_intentos})")
                await asyncio.sleep(espera)
            else:
                print("💥 Demasiados fallos de red. Apagando cliente por seguridad.")

if __name__ == "__main__":
    # Arrancamos el motor
    asyncio.run(cliente_sse_indestructible())