import http.server
import socketserver
import time
import random
import json
import threading

PORT = 9999

class ChaosHandler(http.server.SimpleHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        # Simula latencia aleatoria
        time.sleep(random.uniform(0.1, 0.5))
        
        if "/productos" in self.path:
            # Simula ID 500 lento (Timeout)
            if "500" in self.path:
                time.sleep(15) 
            
            # Simula error 500 en ID 999
            if "999" in self.path:
                self.send_error(500, "Error Interno Simulado")
                return

            self._send_json({"id": 1, "nombre": "Producto Test", "precio": 100.0})
        else:
            self._send_json({"status": "ok"})

    # --- AGREGAMOS ESTOS MÉTODOS PARA QUE NO FALLE EL RETO 3 ---
    def do_POST(self):
        time.sleep(0.2)
        self._send_json({"mensaje": "Producto creado", "id_nuevo": random.randint(1000, 9999)}, status=201)

    def do_PUT(self):
        time.sleep(0.2)
        self._send_json({"mensaje": "Producto actualizado"}, status=200)

    def do_DELETE(self):
        time.sleep(0.2)
        self.send_response(204)
        self.end_headers()

print(f"🤣 Servidor Chaos V2 corriendo en puerto {PORT} (Acepta POST/PUT)...")
# Parche para evitar errores de socket en Windows al cerrar
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), ChaosHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido.")