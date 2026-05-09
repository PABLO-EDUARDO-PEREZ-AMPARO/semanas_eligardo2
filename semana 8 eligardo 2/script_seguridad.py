import base64
import json
import time

def decode_payload(token):
    partes = token.split('.')
    if len(partes) != 3:
        return "Error: Token inválido"
    payload_b64 = partes[1]
    relleno = len(payload_b64) % 4
    if relleno:
        payload_b64 += '=' * (4 - relleno)
    json_data = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
    payload = json.loads(json_data)
    if 'exp' in payload:
        ahora = time.time()
        segundos_restantes = payload['exp'] - ahora
        minutos_restantes = segundos_restantes / 60
        
        print(f"--- Análisis de Token EcoMarket ---")
        print(f"Usuario: {payload.get('sub')}")
        print(f"Tiempo restante: {minutos_restantes:.2f} minutos")
        print(f"------------------------------------")
    return payload
mi_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzQ1NiIsImVtYWlsIjoiYW5hQGVjb21hcmtldC5teCIsInJvbGUiOiJvcGVyYXRvciIsImV4cCI6MTcxNDAwMDAwMCwiaWF0IjoxNzIzOTk5MTAwfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

datos_decodificados = decode_payload(mi_token)