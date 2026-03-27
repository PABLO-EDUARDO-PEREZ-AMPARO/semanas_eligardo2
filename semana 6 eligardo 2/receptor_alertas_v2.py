import asyncio
import httpx


class Observable:
    def __init__(self):
        self.suscriptores = {}

    def suscribir(self, tipo_evento, funcion):
        if tipo_evento not in self.suscriptores:
            self.suscriptores[tipo_evento] = []
        self.suscriptores[tipo_evento].append(funcion)

    def notificar(self, tipo_evento, datos):
        if tipo_evento in self.suscriptores:
            for funcion in self.suscriptores[tipo_evento]:
                try:
                    funcion(datos)
                except Exception as e:
                    print(f"⚠️ Un suscriptor falló ({e}), pero el sistema continúa.")


def ActualizadorPreciosUI(datos):
    print(f"💻 [UI] Tabla actualizada con nuevo precio: {datos.strip()}")

def AlertaStockCritico(datos):
    print(f"🚨 [URGENTE] Parpadeo rojo en pantalla. Faltan unidades: {datos.strip()}")

historial_auditoria = []
def RegistradorAuditoria(datos):
    historial_auditoria.append(datos)
    print(f"📝 [Auditoría] Evento guardado. Total en historial: {len(historial_auditoria)}")



class ReceptorAlertas:
    def __init__(self):
        
        self.tablero_eventos = Observable()

    async def iniciar_conexion(self):
        corriendo = True
        ultimo_id = None
        retry_ms = 5000

        print("🔌 Iniciando Receptor de Alertas SSE v2...")

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
                            print("⏹️ El servidor cerró la conexión (204 No Content).")
                            break

                        buffer = {"id": None, "event": None, "data": ""}

                        async for linea in response.aiter_lines():
                            if linea.startswith(":"):
                                continue

                            if linea == "":
                                if buffer["event"] or buffer["data"]:
                                    
                                    self.tablero_eventos.notificar(buffer["event"], buffer["data"])
                                    
                                    if buffer["id"] is not None:
                                        ultimo_id = buffer["id"]
                                        
                                buffer = {"id": None, "event": None, "data": ""}
                                continue

                            if ":" in linea:
                                clave, valor = linea.split(":", 1)
                                clave, valor = clave.strip(), valor.strip()

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


async def main():
    receptor = ReceptorAlertas()

    
    receptor.tablero_eventos.suscribir("precio-actualizado", ActualizadorPreciosUI)
    receptor.tablero_eventos.suscribir("stock-critico", AlertaStockCritico)
    receptor.tablero_eventos.suscribir("precio-actualizado", RegistradorAuditoria)
    receptor.tablero_eventos.suscribir("stock-critico", RegistradorAuditoria)

   
    await receptor.iniciar_conexion()

if __name__ == "__main__":
    asyncio.run(main())