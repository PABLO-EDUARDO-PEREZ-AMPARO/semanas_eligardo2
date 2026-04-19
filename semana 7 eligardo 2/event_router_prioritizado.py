"""
================================================================================
entregable 5
================================================================================
Elegí utilizar el patrón Decorador/Wrapper (Composición) en lugar de la Herencia.
 La principal ventaja de esta decisión es que "nada más se envuelve" el objeto original.
================================================================================
"""

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
                print(f"Error en handler: {error}")

class EventRouterPrioritizado:
    def __init__(self, router_base):
        self.router_base = router_base
        self.prioridades = {}
        self.cola_eventos = []

    def registrar(self, evento, handler, prioridad=5):
        self.prioridades[evento] = prioridad
        self.router_base.registrar(evento, handler)

    def despachar(self, tipo, datos):
        orden_llegada = len(self.cola_eventos)
        prioridad_asignada = self.prioridades.get(tipo, 5)
        
        self.cola_eventos.append({
            "tipo": tipo,
            "datos": datos,
            "prioridad": prioridad_asignada,
            "orden": orden_llegada
        })

    def despachar_pendientes(self):
        self.cola_eventos.sort(key=lambda x: (-x["prioridad"], x["orden"]))
        
        print("\n=== INICIANDO DESPACHO PRIORITIZADO ===")
        posicion = 1
        for evento in self.cola_eventos:
            print(f"[{posicion}] Ejecutando (Prioridad {evento['prioridad']}): ", end="")
            self.router_base.despachar(evento["tipo"], evento["datos"])
            posicion += 1
            
        self.cola_eventos = []

def handler_precio(datos):
    print(f"Módulo Precios -> {datos}")

def handler_stock(datos):
    print(f"Módulo Stock   -> ¡URGENTE! {datos}")

def handler_ping(datos):
    print(f"Módulo Sistema -> Ping recibido: {datos}")

if __name__ == "__main__":
    router_original = event_router()
    router_pro = EventRouterPrioritizado(router_original)

    router_pro.registrar("stock-critico", handler_stock, prioridad=10)
    router_pro.registrar("precio-actualizado", handler_precio) 
    router_pro.registrar("sistema-ping", handler_ping, prioridad=1)

    print("Simulando llegada de 15 eventos al stream...")
    
    for i in range(1, 10): 
        router_pro.despachar("precio-actualizado", f"Actualización {i}")
        
    router_pro.despachar("stock-critico", "Inventario en ceros") 
    
    for i in range(10, 14): 
        router_pro.despachar("precio-actualizado", f"Actualización {i}")
        
    router_pro.despachar("sistema-ping", "Latencia estable") 

    router_pro.despachar_pendientes()