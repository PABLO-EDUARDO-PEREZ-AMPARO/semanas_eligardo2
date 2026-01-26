import requests
import os
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# IMPORTAMOS EL LOGGER QUE ACABAMOS DE CREAR
from eco_logger import auditar_peticion_http, logger

# --- CONFIGURACIÓN ---
BASE_URL = os.getenv("ECOMARKET_API_URL", "http://localhost:9999") 
TOKEN = os.getenv("ECOMARKET_TOKEN", "token_dummy_seguro")
TIMEOUT_GLOBAL = 5

# --- CAPA DE CONEXIÓN (Session + Retry) ---
def crear_sesion_resiliente():
    session = requests.Session()
    # Estrategia: Reintentar 3 veces si el servidor falla (500, 503, etc.)
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

http = crear_sesion_resiliente()

# --- CAPA TÉCNICA (Decorada con Logs) ---

@auditar_peticion_http  # <--- ¡AQUÍ ESTÁ LA MAGIA!
def _ejecutar_raw_request(method, url, json_data=None, headers=None):
    """Ejecuta la petición cruda. El decorador se encarga de medir y loguear."""
    return http.request(
        method=method,
        url=url,
        json=json_data,
        headers=headers,
        timeout=TIMEOUT_GLOBAL
    )

# --- CAPA DE NEGOCIO ---

def realizar_request(metodo, endpoint, datos=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "EcoMarketClient/Pro"
    }

    try:
        # 1. Llamada a la red
        response = _ejecutar_raw_request(metodo, url, json_data=datos, headers=headers)
        
        # 2. Validaciones de negocio
        response.raise_for_status() # Lanza error si es 4xx o 5xx
        
        if not response.content:
            return None
            
        return response.json()

    except requests.exceptions.JSONDecodeError:
        logger.error(f"Formato inválido (HTML o XML) recibido de {url}")
        return None
    except requests.exceptions.HTTPError:
        # El log detallado ya lo escribió el decorador. Aquí silenciamos el error.
        return None
    except Exception as e:
        logger.critical(f"💥 Error inesperado en el cliente: {e}")
        return None

# --- PRUEBAS ---

def listar_productos():
    # Prueba cambiar la ruta a "/flaky" o "/slow" para ver distintos logs
    ruta = "/flaky" 
    print(f"\n--- Probando '{ruta}' ---")
    data = realizar_request("GET", ruta)
    if data: print(f"📦 Respuesta: {data}")

def crear_producto(prod):
    print(f"\n--- Intentando crear producto ---")
    data = realizar_request("POST", "/productos", prod)
    if data: print(f"✨ Creado ID: {data.get('id')}")

if __name__ == "__main__":
    print("🔭 CLIENTE OBSERVABLE LISTO\n")
    listar_productos()
    
    nuevo = {"nombre": "Test Log", "precio": 99}
    crear_producto(nuevo)