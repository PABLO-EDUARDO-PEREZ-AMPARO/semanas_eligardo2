import http.server
import socketserver
import json
import time
import threading  # <--- ESTO ES IMPORTANTE

PORT = 9999

PRODUCTOS = {
    1: {"id": 1, "nombre": "Miel Orgánica", "precio": 150.0},
    2: {"id": 2, "nombre": "Mermelada Fresa", "precio": 85.5},
    3: {"id": 3, "nombre": "Pan Artesanal", "precio": 45.0},
    4: {"id": 4, "nombre": "Queso de Cabra", "precio": 120.0},
}

class ChaosHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/productos/"):
            try:
                prod_id = int(self.path.split("/")[-1])
            except ValueError:
                self.send_error(400, "ID invalido")
                return

            # CASO LENTO
            if prod_id == 500:
                time.sleep(5) 
                self.send_error(408, "Timeout simulado")
                return

            # CASO ERROR
            if prod_id == 999:
                self.send_error(500, "Error Interno del Servidor")
                return

            # CASO ÉXITO
            producto = PRODUCTOS.get(prod_id)
            if producto:
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(producto).encode())
            else:
                self.send_error(404, "Producto no encontrado")
        else:
            self.send_error(404, "Ruta desconocida")

# --- ESTA PARTE ES LA CLAVE PARA QUE NO SE BLOQUEE ---
class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
# -----------------------------------------------------

print(f"🤣 Servidor del Caos (Multi-hilo) corriendo en puerto {PORT}...")
with ThreadedHTTPServer(("", PORT), ChaosHandler) as httpd:
    httpd.serve_forever()