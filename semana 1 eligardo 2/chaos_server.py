from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import random

# Configuración
HOST = "localhost"
PORT = 9999
request_count = 0

class ChaosHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global request_count
        request_count += 1
        
        # Escenario 1 y 5: Timeout / Red Lenta (/slow)
        if self.path == "/slow":
            time.sleep(10) # Duerme 10 segundos
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "Llegue tarde pero llegue"}')

        # Escenario 2: Intermitencia (/flaky)
        elif self.path == "/flaky":
            if request_count % 3 == 0:
                self.send_error(503, "Service Unavailable (Falla simulada)")
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status": "Todo bien"}')

        # Escenario 3: Respuesta Truncada (/truncated)
        elif self.path == "/truncated":
            self.send_response(200)
            self.send_header('Content-Length', '1000') # Mentimos sobre el tamaño
            self.end_headers()
            self.wfile.write(b'{"status": "Cortan') # Enviamos poco y...
            # ... NO cerramos bien, o cerramos abruptamente la conexión.
            return # Se corta el flujo aquí

        # Escenario 4: Formato Inesperado (/html)
        elif self.path == "/html":
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Soy HTML, no JSON</h1></body></html>")

        # Ruta normal para verificar que funciona
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"id": 1, "nombre": "Producto Normal", "precio": 10}')

print(f"🔥 Servidor del Caos activo en http://{HOST}:{PORT}")
httpd = HTTPServer((HOST, PORT), ChaosHandler)
httpd.serve_forever()

