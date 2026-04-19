import time

# ==========================================
# DEPENDENCIA: El Router (Maneja los handlers)
# ==========================================
class EventRouter:
    def __init__(self):
        self.handlers = {}

    def registrar(self, evento, handler):
        self.handlers[evento] = handler

    def despachar(self, tipo, datos):
        if tipo in self.handlers:
            # ETAPA 2: La red de seguridad (try/except)
            try:
                self.handlers[tipo](datos)
            except Exception as error:
                # Atrapamos el error, el programa no hace Crash.
                print(f"⚠️ Alerta CRÍTICA: El handler '{tipo}' falló. Detalle: {error}")
        else:
            pass # Si no hay suscriptor, lo ignoramos en silencio (Patrón Dispara y Olvida)

# ==========================================
# ETAPA 1: El Cliente SSE Multiplexado
# ==========================================
class ClienteSSEMultiplex:
    def __init__(self, modulos, router):
        self.modulos = modulos
        self.router = router
        self.estado = "DESCONECTADO"
        self.ultimo_id = None

    # PARTE 1: Validar URL (INV-C3)
    def construir_url(self):
        if not self.modulos:
            raise ValueError("Error: La lista de módulos no puede estar vacía (INV-C3).")
        modulos_str = ",".join(self.modulos)
        return f"https://api.ecomarket.com/eventos?modulos={modulos_str}"

    # PARTE 5: Máquina de estados y protección de dobles clics (INV-C1)
    def iniciar(self):
        if self.estado in ["CONECTANDO", "CONECTADO"]:
            print("Aviso: El cliente ya está en uso. Ignorando doble llamada (INV-C1).")
            return
        
        self.estado = "CONECTANDO"
        print(f"🌐 Iniciando conexión a: {self.construir_url()}\n" + "-"*40)
        self._conectar()

    def _conectar(self):
        self.estado = "CONECTADO"
        # Aquí iría tu código real con httpx o aiohttp. 
        # Para esta prueba, simularemos la red con una lista de textos:
        stream_simulado = [
            "event: precio-actualizado", 'data: {"precio": 50}', "",
            "event: stock-critico", 'data: {"quedan": 5}', "",
            ": esto es un comentario de la red, debe ignorarse",
            "data: ping del sistema (no tiene evento)", "",
            "event: precio-actualizado", 'data: JSON_CORRUPTO_EXPLOSIVO', "", # <-- Evento #5 que falla
            "event: stock-critico", 'data: {"quedan": 1}', ""                 # <-- Evento #6 que debe salvarse
        ]
        self._leer_stream(stream_simulado)
        self.estado = "DESCONECTADO"

    # PARTE 4: Bucle de lectura
    def _leer_stream(self, stream):
        buffer_evento = {}
        for linea in stream:
            # 1. ¿Línea en blanco? Procesamos y limpiamos
            if linea == "":
                if buffer_evento:
                    self._procesar_evento(buffer_evento)
                    buffer_evento = {} # Limpiamos para el que sigue
            else:
                # 2. Si hay texto, lo parseamos y lo guardamos en el buffer
                clave, valor = self._parsear_linea(linea)
                if clave: # Si no es None (comentarios)
                    buffer_evento[clave] = valor

    # PARTE 2: Extraer la información
    def _parsear_linea(self, linea):
        if not linea or linea.startswith(":"):
            return None, None # Ignoramos comentarios vacíos
        
        if ":" not in linea:
            return linea.strip(), "" # Si no hay valor, mandamos string vacío
            
        clave, valor = linea.split(":", 1) # El truco del "1" para no romper los JSON
        return clave.strip(), valor.strip()

    # PARTE 3: Despachar
    def _procesar_evento(self, buffer_evento):
        # Si no tiene nombre de evento, le ponemos "message" por defecto (INV-C2)
        tipo = buffer_evento.get("event", "message")
        datos = buffer_evento.get("data", "")
        
        # Guardamos el ID por si la red se cae (reconexión)
        if "id" in buffer_evento:
            self.ultimo_id = buffer_evento["id"]
            
        self.router.despachar(tipo, datos)

# ==========================================
# ETAPA 2: Flujo Real de EcoMarket
# ==========================================

# 1. Creamos nuestros Handlers (Departamentos)
def handler_precio(datos):
    if datos == "JSON_CORRUPTO_EXPLOSIVO":
        raise ValueError("¡No se pudo leer el JSON del Precio!")
    print(f"💰 PRECIO: {datos}")

def handler_stock(datos):
    print(f"📦 STOCK URGENTE: {datos}")

def handler_heartbeat(datos):
    print(f"💓 PING (evento sin nombre): {datos}")

# 2. Bloque principal de ejecución
if __name__ == "__main__":
    # Creamos el router y registramos los departamentos
    mi_router = EventRouter()
    mi_router.registrar("precio-actualizado", handler_precio)
    mi_router.registrar("stock-critico", handler_stock)
    mi_router.registrar("message", handler_heartbeat) # Registramos el tipo por defecto (INV-C2)
    
    # Instanciamos el cliente con los módulos (INV-C3)
    cliente = ClienteSSEMultiplex(["precios", "inventario", "pedidos"], mi_router)
    
    # Arrancamos la máquina
    cliente.iniciar()