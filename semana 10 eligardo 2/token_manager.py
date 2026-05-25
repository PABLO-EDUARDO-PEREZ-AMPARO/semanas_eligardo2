import base64
import json
import time

class TokenManager:
    def __init__(self, token="inicial.token.payload", refresh_token="refresh_dummy"):
        self._token = token
        self._refresh_token = refresh_token

    def get_access_token(self):
        return self._token

    def is_expiring_soon(self):
        try:
            partes = self._token.split('.')
            if len(partes) != 3:
                return True  # No es un JWT válido, requiere renovación inmediata
            
            payload_b64 = partes[1]
            # Ajuste de padding automático para Base64 estándar
            payload_b64 += '=' * (-len(payload_b64) % 4)
            payload_json = base64.b64decode(payload_b64).decode('utf-8')
            payload = json.loads(payload_json)
            
            exp = payload.get('exp', 0)
            return time.time() >= (exp - 30)  # Margen de seguridad de 30 segundos
        except Exception:
            # Captura segura de errores de decodificación para evitar activar el Hard Gate
            return True

    async def refresh_access_token(self):
        print("🔄 [TM] Renovando token de acceso...")
        self._token = "nuevo.token.renovado"
        return self._token