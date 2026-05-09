import base64
import json
import time
import threading

class MockServer:
    def __init__(self):
        self.token_actual = "token_inicial"
        self.contador_refresh = 0  

    def procesar_peticion(self, endpoint, headers=None, body=None):
        print(f"🌐 [Red] Petición a {endpoint}...")
        time.sleep(0.5) 

        if "refresh" in endpoint:
            self.contador_refresh += 1
            if body and body.get("refresh_token") == "refresh_valido":
                self.token_actual = f"token_nuevo_{int(time.time())}"
                return 200, {"access_token": self.token_actual}
            return 401, {"error": "Refresh expirado"}

      
        auth_header = headers.get("Authorization", "") if headers else ""
        if auth_header == f"Bearer {self.token_actual}":
            return 200, {"data": "Petición exitosa, aquí están tus datos."}
        return 401, {"error": "Token inválido o expirado"}

api_mock = MockServer()
class TokenManager:
    def __init__(self):
        self._access_token = None
        self._refresh_token = None
        self._lock = threading.Lock()
        self._timer = None 
        self._detener_timer = threading.Event()
    def store_tokens(self, access_token, refresh_token):
        """Almacena tokens y arranca el monitor proactivo (Nivel Extendido)."""
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._detener_timer.clear()
        self._timer = threading.Thread(target=self._monitor_proactivo, daemon=True)
        self._timer.start()
    def get_auth_header(self):
        """Devuelve el header formateado si hay token."""
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}
    def decode_payload(self):
        if not self._access_token:
            return None
        partes = self._access_token.split('.')
        if len(partes) != 3:
            return None
        
        payload_b64 = partes[1]
        relleno = len(payload_b64) % 4
        if relleno:
            payload_b64 += '=' * (4 - relleno)
            
        try:
            return json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        except Exception:
            return None
    def is_expiring_soon(self):
        payload = self.decode_payload()
        if not payload or 'exp' not in payload:
            return True
        return (payload['exp'] - time.time()) < 300
    def refresh_access_token(self):
        """Implementa patrón Singleton con Double-Checked Locking."""
        if self.is_expiring_soon():
            with self._lock:
                
                if self.is_expiring_soon():
                    print("🔄 [Manager] Entrando a Lock crítico para hacer Refresh...")
                    status, respuesta = api_mock.procesar_peticion(
                        "/api/auth/refresh", 
                        body={"refresh_token": self._refresh_token}
                    )
                    
                    if status == 200:
                        self._access_token = respuesta["access_token"]
                        print("✅ [Manager] Refresh exitoso.")
                        return True
                    else:
                        print("❌ [Manager] Falló el refresh. Sesión muerta.")
                        self.logout()
                        return False
        return True

    def _monitor_proactivo(self):
        """Nivel Extendido: Timer que revisa el token en segundo plano."""
        while not self._detener_timer.is_set():
            if self._access_token and self.is_expiring_soon():
                print("⏰ [Timer Proactivo] Detectada ventana de expiración. Renovando...")
                self.refresh_access_token()
            time.sleep(5) 

    def logout(self):
        """Limpia estado y mata timers zombies."""
        self._access_token = None
        self._refresh_token = None
        self._detener_timer.set()
        print("🚪 [Manager] Logout completado. Timer proactivo apagado.")

manager = TokenManager()
def auth_request(metodo, url, body=None):
    headers = manager.get_auth_header()
    status, respuesta = api_mock.procesar_peticion(url, headers=headers, body=body)
    
    if status == 401:
        
        if "refresh" in url:
            manager.logout()
            return status, respuesta
            
        if manager.refresh_access_token():
            print("🔁 [Interceptor] Reintentando petición original...")
            nuevos_headers = manager.get_auth_header()
            
            status_reintento, respuesta_reintento = api_mock.procesar_peticion(url, headers=nuevos_headers, body=body)
            
            if status_reintento == 401:
                print("❌ [Interceptor] El reintento también falló con 401. Logout definitivo.")
                manager.logout()
                
            return status_reintento, respuesta_reintento
           
        else:
            
            manager.logout()
            
    return status, respuesta
if __name__ == "__main__":
    print("\n--- INICIO DE DEMOSTRACIÓN ---")
    print("\n[Paso 1] Login Simulado y Store Tokens")
    expiracion_inmediata = int(time.time()) + 10
    payload = {"sub": "user_123", "exp": expiracion_inmediata}
    token_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    token_simulado = f"header.{token_b64}.signature"
    
    manager.store_tokens(token_simulado, "refresh_valido")
    api_mock.token_actual = token_simulado 
    
    print("\n[Paso 2] Petición Autenticada Normal")
    auth_request("GET", "/api/ecomarket/productos")
    
    print("\n[Paso 3] Simular 401 cambiando el token del servidor")
    api_mock.token_actual = "el_token_expiró_en_backend"
    
    print("\n[Paso 4] Disparar petición que fallará y causará refresh + reintento")
    auth_request("GET", "/api/ecomarket/perfil")
    
    print("\n[Paso 5] Demostración de Nivel Extendido: Refresh Singleton (Thundering Herd)")
    manager.store_tokens(token_simulado, "refresh_valido")
    hilos = []
    for i in range(5):
        h = threading.Thread(target=auth_request, args=("GET", f"/api/ecomarket/carrito_{i}"))
        hilos.append(h)
        h.start()
    for h in hilos:
        h.join()
        
    print(f" Llamadas reales al servidor de refresh: {api_mock.contador_refresh} (Debe ser 1 por cada evento de expiración)")

    print("\n[Paso 6] Logout y limpieza final")
    manager.logout()