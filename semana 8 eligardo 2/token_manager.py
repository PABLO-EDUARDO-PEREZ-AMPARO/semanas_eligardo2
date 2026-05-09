import base64
import json
import time
import threading
import requests

class TokenManager:
    def __init__(self, refresh_url):
        self._access_token = None
        self._refresh_token = None
        self._refresh_url = refresh_url
        self._lock = threading.Lock() # Nuestro candado para el patrón Singleton
    def set_tokens(self, access_token, refresh_token):
        """Almacena los tokens iniciales tras un login exitoso."""
        self._access_token = access_token
        self._refresh_token = refresh_token
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
            json_data = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
            return json.loads(json_data)
        except Exception:
            return None
    def is_expiring_soon(self):
        payload = self.decode_payload()
        if not payload or 'exp' not in payload:
            return True 
        segundos_restantes = payload['exp'] - time.time()
        return segundos_restantes < 300

    def refresh_access_token(self):
        if self.is_expiring_soon():
            with self._lock:
                if self.is_expiring_soon():
                    print("🔄 [Sistema] Ejecutando Silent Refresh de forma segura...")
                    
                    if not self._refresh_token:
                        self.logout()
                        return False
                        
                    try:
                        nuevo_exp = int(time.time()) + 900 
                        payload_simulado = {"sub": "pablo_dev", "exp": nuevo_exp}
                        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_simulado).encode()).decode().rstrip('=')
                        self._access_token = f"fakeHeader.{payload_b64}.fakeSignature"
                        print("✅ [Sistema] ¡Refresh exitoso! Nuevo token obtenido.")
                        
                        return True
                    except Exception as e:
                        print(f"❌ [Sistema] Error en refresh: {e}")
                        self.logout()
                        return False
        return True 

    def logout(self):
        self._access_token = None
        self._refresh_token = None
        print("🚪 [Sistema] Sesión cerrada. Datos eliminados de la memoria.")
if __name__ == "__main__":
    print("=== INICIANDO PRUEBA DE TOKEN MANAGER ===")
    manager = TokenManager(refresh_url="http://api.ecomarket.mx/refresh")
    tiempo_expiracion = int(time.time()) + 120
    payload_dict = {"sub": "pablo_dev", "role": "admin", "exp": tiempo_expiracion}
    payload_codificado = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode().rstrip('=')
    jwt_simulado = f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{payload_codificado}.firma_falsa_123"
    print("\n[Paso 1] Usuario hace Login exitoso.")
    manager.set_tokens(access_token=jwt_simulado, refresh_token="refresh_secreto_7dias")
    datos = manager.decode_payload()
    print("\n[Paso 2] Decodificando Payload...")
    if datos:
        minutos_restantes = (datos['exp'] - time.time()) / 60
        print(f"   -> Usuario: {datos.get('sub')}")
        print(f"   -> Rol: {datos.get('role')}")
        print(f"   -> Tiempo restante: {minutos_restantes:.2f} minutos")
    print("\n[Paso 3] El interceptor HTTP va a hacer una petición y revisa el token...")
    if manager.is_expiring_soon():
        print("   -> ¡Alerta! El token expira en menos de 5 minutos.")
        manager.refresh_access_token()
        datos_nuevos = manager.decode_payload()
        nuevos_minutos = (datos_nuevos['exp'] - time.time()) / 60
        print(f"   -> Nuevo tiempo restante tras refresh: {nuevos_minutos:.2f} minutos")
    else:
        print("   -> El token está sano, procediendo con la petición.")
    print("\n[Paso 4] El usuario hace clic en 'Cerrar Sesión'...")
    manager.logout()
    print("=== FIN DE LA PRUEBA ===")