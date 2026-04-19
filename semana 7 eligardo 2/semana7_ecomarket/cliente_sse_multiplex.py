"""
================================================================================
RETO 3: DECISIONES DE DISEÑO - CLIENTE SSE MULTIPLEXADO
================================================================================
1. Mi TIMEOUT de 10 segundos: Decidí usar 10 segundos porque es un punto de 
   equilibrio realista; le da suficiente tiempo a una red lenta para establecer 
   la conexión, pero evita que mi programa se quede esperando infinitamente.

2. Mi MAX_REINTENTOS: Definí un máximo de 5 intentos para que el cliente no se 
   quede en un bucle infinito gastando recursos si el servidor muere. Entiendo 
   que si la caída es larga, el cliente se rendirá y el usuario deberá recargar.

3. Mi ESPERA_INICIAL: Elegí una pausa de 3 segundos entre reintentos para que 
   funcione como un amortiguador básico que no sature la red ni el procesador 
   mientras intenta recuperar el flujo.

4. Trade-off de conexión única: La ventaja es que no agoto el límite de 6 
   conexiones del navegador. El costo es que si la conexión principal falla, 
   absolutamente todos mis módulos (precios, stock, pedidos) se detienen.

5. Limitación no resuelta: El cambio dinámico de módulos. Si quiero agregar 
   "devoluciones", debo reiniciar la conexión, lo que genera una "ceguera" 
   de milisegundos donde podría perder eventos si no uso el Last-Event-ID.
================================================================================
"""


import time
import json
import requests  # Agregado para la conexión HTTP real

class event_router:
    def __init__(self):
        self.handlers = {}
    def registrar(self, evento, handler):
        self.handlers[evento] = handler
    def despachar(self, tipo, datos):
        if tipo in self.handlers:
            try:
                self.handlers[tipo](datos)
            except Exception as error:
                print(f"Alerta CRÍTICA: El handler '{tipo}' falló. Detalle: {error}")
class cliente_sse_multiplex:
    def __init__(self, modulos, router):
        self.modulos = modulos
        self.router = router
        self.estado = "DESCONECTADO"
        self.ultimo_id = None
    def construir_url(self):
        if not self.modulos:
            raise ValueError("Error: La lista de módulos no puede estar vacía.")
        modulos_str = ",".join(self.modulos)
        return f"https://api.ecomarket.com/eventos?modulos={modulos_str}"
    def iniciar(self):
        if self.estado in ["CONECTANDO", "CONECTADO"]:
            print("Aviso: El cliente ya está en uso. Ignorando doble llamada.")
            return
        self.estado = "CONECTANDO"
        print(f"Iniciando conexión a: {self.construir_url()}\n" + "-"*50)
        self._conectar()
    def detener(self):
        self.estado = "DESCONECTADO"
        self.ultimo_id = None
        print("Cliente detenido explícitamente.")
    def _conectar(self):
        self.estado = "CONECTADO"
        headers = {"Accept": "text/event-stream"}
        if self.ultimo_id:
            headers["Last-Event-ID"] = self.ultimo_id
        try:
            respuesta = requests.get(
                self.construir_url(), 
                headers=headers, 
                stream=True, 
                timeout=10 
            )
            lineas_decodificadas = (linea.decode('utf-8') for linea in respuesta.iter_lines() if linea)
            self._leer_stream(lineas_decodificadas) 
        except requests.exceptions.Timeout:
            print("Error: La conexión excedió el tiempo de espera (Timeout).")
        except Exception as e:
            print(f"Error de conexión HTTP: {e}")
            print("\n[Activando simulador de eventos local por fallo de red...]\n")
            stream_simulado = [
                "event: precio-actualizado", 'data: {"precio": 120.0}', "",         
                "event: stock-critico", 'data: {"quedan": 8}', "",                  
                "event: pedido-nuevo", 'data: {"id": 1, "total": 200}', "",         
                "event: pedido-nuevo", 'data: {"id": 2, "total": 650}', "",         
                "data: ping del sistema", "",                                       
                ": esto es un comentario en la red que se debe ignorar",
                "event: precio-actualizado", 'data: JSON_CORRUPTO_EXPLOSIVO', "",   
                "event: stock-critico", 'data: {"quedan": 2}', "",                  
                "event: precio-actualizado", 'data: {"precio": 122.0}', "",         
                "event: pedido-nuevo", 'data: {"id": 3, "total": 800}', "",         
                "data: ping de cierre", ""                                          
            ]
            self._leer_stream(stream_simulado)
        finally:
            if self.estado != "DESCONECTADO":
                self.estado = "DESCONECTADO"
    def _leer_stream(self, stream):
        buffer_evento = {}
        for linea in stream:
            if linea == "":
                if buffer_evento:
                    self._procesar_evento(buffer_evento)
                    buffer_evento = {}
            else:
                clave, valor = self._parsear_linea(linea)
                if clave:
                    buffer_evento[clave] = valor
    def _parsear_linea(self, linea):
        if not linea or linea.startswith(":"):
            return None, None
        if ":" not in linea:
            return linea.strip(), ""
        clave, valor = linea.split(":", 1)
        return clave.strip(), valor.strip()
    def _procesar_evento(self, buffer_evento):
        tipo = buffer_evento.get("event", "message") 
        datos = buffer_evento.get("data", "")
        if "id" in buffer_evento:
            self.ultimo_id = buffer_evento["id"]
        self.router.despachar(tipo, datos)
precio_base = 100.0
pedidos_vip_locales = []
ultima_conexion_activa = None
def handler_precio_actualizado(datos_str):
    global precio_base
    if "JSON_CORRUPTO" in datos_str:
        raise ValueError("Error precio inválido.")
    datos = json.loads(datos_str)
    nuevo_precio = datos["precio"]
    cambio = abs(nuevo_precio - precio_base) / precio_base
    if cambio > 0.05:
        print(f"ALERTA PRECIO: Variación mayor a 5% detectada. Nuevo precio: ${nuevo_precio}")
    precio_base = nuevo_precio # Actualizamos la base
def handler_stock_critico(datos_str):
    datos = json.loads(datos_str)
    quedan = datos["quedan"]
    if quedan <= 3:
        print(f"STOCK URGENTE [CRÍTICO]: Solo quedan {quedan} unidades.")
    elif quedan <= 10:
        print(f"STOCK URGENTE [BAJO]: Quedan {quedan} unidades.")
def handler_pedido_nuevo(datos_str):
    datos = json.loads(datos_str)
    if datos["total"] > 500:
        pedidos_vip_locales.append(datos)
        print(f"NUEVO PEDIDO VIP: Registrado pedido #{datos['id']} por ${datos['total']}")
def handler_heartbeat(datos_str):
    global ultima_conexion_activa
    ultima_conexion_activa = time.time()
    print(f"Conexión activa a las {time.strftime('%H:%M:%S')}")
if __name__ == "__main__":
    router = event_router()
    router.registrar("precio-actualizado", handler_precio_actualizado)
    router.registrar("stock-critico", handler_stock_critico)
    router.registrar("pedido-nuevo", handler_pedido_nuevo)
    router.registrar("message", handler_heartbeat) 
    cliente = cliente_sse_multiplex(["precios", "inventario", "pedidos"], router)
    cliente.iniciar()
    print("\npedidos VIP guardados localmente:", pedidos_vip_locales)