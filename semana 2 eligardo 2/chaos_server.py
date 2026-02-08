import http.server
import socketserver
import random
import time
import json
from datetime import datetime

PORT = 9999

# Datos simulados con estructura compleja para probar validación
# El último producto tiene errores a propósito (precio negativo, falta productor)
DATA_PRODUCTOS =  [ 

    {
        "id": 1, 
        "nombre": "Miel Orgánica", 
        "precio": 150.00, 
        "categoria": "miel",
        "productor": {"id": 7, "nombre": "Apiarios del Valle"},
        "disponible": True,
        "creado_en": "2024-01-15T10:30:00Z"
    },
    {
        "id": 2, 
        "nombre": "Mermelada de Fresa", 
        "precio": 85.50, 
        "categoria": "conservas",
        "productor": {"id": 8, "nombre": "Dulces Caseros"},
        "disponible": True,
        "creado_en": "2024-02-01T09:00:00Z"
    },
    {
        # este lo iso la ia
        "id": 4, 
        "nombre": "Producto Corrupto (Trampa)", 
        "precio": -10.00, # ERROR: Precio negativo
        "categoria": "wasavi", # ERROR: Categoría inválida
        "disponible": True, # ERROR: No es booleano
        "creado_en": "mañana" # ERROR: Fecha mala
    },
     {
        # este lo ise yo
        "id": 5, 
        "nombre": "las palmas", 
        "precio": -777.00, # ERROR: Precio negativo
        "categoria": "jalapa", # ERROR: Categoría inválida
        "disponible": True, # ERROR: No es booleano
        "creado_en": "el otro dia " # ERROR: Fecha mala
    }
]

class ChaosHandler(http.server.SimpleHTTPRequestHandler):
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def simulate_chaos(self):
        val = random.random()
        if val < 0.1:  # 10% error 500
            self.send_error(500, "Simulated Internal Server Error")
            return True
        elif val < 0.2:  # 10% lentitud
            time.sleep(1.5)
        return False

    def do_GET(self):
        if self.simulate_chaos(): return

        if self.path == "/productos":
            self.send_json_response(DATA_PRODUCTOS)
        elif self.path.startswith("/productos/"):
            # Devuelve siempre el primero para simplificar la demo de GET individual
            self.send_json_response(DATA_PRODUCTOS[0])
        else:
            self.send_error(404, "Ruta no encontrada")

    def do_POST(self):
        if self.simulate_chaos(): return
        if self.path == "/productos":
            self.send_json_response({"id": 99, "status": "creado"}, status=201)
        else:
            self.send_error(404, "No encontrado")

    def do_PUT(self):
        if self.simulate_chaos(): return
        if self.path.startswith("/productos/"):
            self.send_json_response({"status": "Actualizado totalmente (PUT)"})
        else:
            self.send_error(405)

    def do_PATCH(self):
        if self.simulate_chaos(): return
        if self.path.startswith("/productos/"):
            self.send_json_response({"status": "Actualizado parcialmente (PATCH)"})
        else:
            self.send_error(405)

    def do_DELETE(self):
        if self.simulate_chaos(): return
        if self.path.startswith("/productos/"):
            self.send_json_response({"status": "Eliminado correctamente"})
        else:
            self.send_error(405)

print(f"🔥 Servidor Chaos (Semana 2 + Datos Complejos) en http://localhost:{PORT}")
socketserver.TCPServer(("", PORT), ChaosHandler).serve_forever()