import time

class MockResponse:
    def __init__(self, status_code, json_data, url):
        self.status_code = status_code
        self._json = json_data
        self.url = url
        
    def json(self):
        return self._json
class MockRequests:
    """Simula el comportamiento de la librería 'requests' y nuestro servidor backend"""
    def __init__(self):
        self.token_servidor = "token_viejo" 

    def request(self, method, url, headers=None, json=None):
        print(f"   [Red] Enviando {method} a {url}...")
        if "refresh" in url:
            if json and json.get("refresh_token") == "refresh_expirado":
                return MockResponse(401, {"error": "Refresh token expirado"}, url)
            self.token_servidor = "TOKEN_NUEVO_Y_BRILLANTE"
            return MockResponse(200, {"access_token": self.token_servidor}, url)
        auth_header = headers.get("Authorization", "") if headers else ""
        if auth_header == f"Bearer {self.token_servidor}":
            return MockResponse(200, {"producto": "Paneles Solares", "precio": "$5000"}, url)
        else:
            return MockResponse(401, {"error": "Token expirado o inválido"}, url)
mock_requests = MockRequests()
class TokenManager:
    def __init__(self):
        self.access_token = "token_viejo" 
        self.refresh_token = "refresh_valido"
        self.refresh_url = "http://api.ecomarket.mx/auth/refresh"

    def refresh_access_token(self):
        """Simula la lógica de renovación que construiste en la Actividad 3"""
        print("🔄 [Manager] Intentando renovar el access_token...")
        respuesta = mock_requests.request(
            "POST", 
            self.refresh_url, 
            json={"refresh_token": self.refresh_token}
        )
        
        if respuesta.status_code == 200:
            self.access_token = respuesta.json()["access_token"]
            print("✅ [Manager] Refresh exitoso. Nuevo token guardado.")
            return True
        return False

    def logout(self):
        print("🚪 [Manager] Cerrando sesión y limpiando tokens (Logout)...")
        self.access_token = None
        self.refresh_token = None

manager = TokenManager()
def auth_request(metodo, url, **kwargs):
    if manager.access_token:
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Authorization'] = f"Bearer {manager.access_token}"
    respuesta = mock_requests.request(metodo, url, **kwargs)
    if respuesta.status_code == 401:
        print(f"⚠️ [Interceptor] Detectado error 401 en {url}")
        if "refresh" in url:
            print("❌ [Interceptor] El refresh token fue rechazado. Abortando.")
            manager.logout()
            return respuesta
        exito = manager.refresh_access_token()
        
        if exito:
            print("🔁 [Interceptor] Reintentando la petición original con el nuevo token...")
            kwargs['headers']['Authorization'] = f"Bearer {manager.access_token}"
            return mock_requests.request(metodo, url, **kwargs)
        else:
            print("❌ [Interceptor] No se pudo renovar el token. Forzando logout.")
            manager.logout()
    return respuesta
if __name__ == "__main__":
    print("=== ESCENARIO 1: Refresh exitoso y reintento ===")
    mock_requests.token_servidor = "token_diferente_en_bd" 
    
    respuesta = auth_request("GET", "http://api.ecomarket.mx/precios")
    print(f"Resultado final: {respuesta.status_code} - {respuesta.json()}\n")
    print("=== ESCENARIO 2: Loop Infinito (Refresh también devuelve 401) ===")
    manager.refresh_token = "refresh_expirado"
    manager.access_token = "token_roto" 
    
    respuesta_fallida = auth_request("GET", "http://api.ecomarket.mx/precios")
    print(f"Resultado final: {respuesta_fallida.status_code} - {respuesta_fallida.json()}")