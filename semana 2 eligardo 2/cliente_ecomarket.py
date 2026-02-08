import os
import requests
from typing import List, Optional
from pydantic import ValidationError

# --- IMPORTACIONES PROPIAS ---
from modelos import Producto
from url_builder import URLBuilder
# Importamos tu decorador manual
from resiliencia import with_retry 

# --- CONFIGURACIÓN ---
RAW_BASE_URL = os.getenv("ECOMARKET_API_URL", "http://localhost:9999")
TOKEN = os.getenv("ECOMARKET_TOKEN", "token_seguro")

# --- EXCEPCIONES ---
class EcoMarketError(Exception): """Error base"""
class ErrorValidacion(EcoMarketError): """El servidor envió datos que no cumplen el esquema"""
class ErrorRed(EcoMarketError): """Timeouts o fallos de conexión"""
class ErrorNegocio(EcoMarketError): """Errores 4xx lógicos"""

class EcoMarketClient:
    def __init__(self, base_url: str, token: str, timeout: int = 5):
        self.url_tool = URLBuilder(base_url)
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        # YA NO usamos _configurar_sesion con HTTPAdapter porque usamos nuestro decorador
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    # ---------------------------------------------------------
    # AQUI ESTÁ LA CLAVE: Decoramos el método central _request
    # ---------------------------------------------------------
    @with_retry(max_retries=3, base_delay=1)
    def _request(self, method: str, endpoint: str, path_params: list = None, data: dict = None):
        """Método centralizado con manejo de errores robusto y reintentos manuales."""
        
        # 1. Construcción Segura de URL
        url = self.url_tool.construir(endpoint, path_params=path_params)
        
        # Nota: Quitamos el try/except gigante aquí para dejar que el decorador
        # capture las excepciones de conexión (ConnectionError, Timeout, 5xx)
        # y decida si reintentar. Solo capturamos lo que NO queremos reintentar.

        try:
            # 2. Ejecución
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout
            )
            
            # 3. Manejo especial de 404 (No es error, es ausencia)
            if response.status_code == 404:
                return None

            # 4. Esto lanzará error en 4xx y 5xx. 
            # El decorador @with_retry atrapará los 5xx y reintentará.
            # Los 4xx pasarán directo (excepto si el decorador dice lo contrario).
            response.raise_for_status()
            
            # 5. Retorno de datos
            if response.status_code != 204: 
                return response.json()
            return {}

        except requests.exceptions.JSONDecodeError:
            # Esto no se reintenta, es error fatal
            raise ErrorRed(f"El servidor devolvió una respuesta corrupta (no es JSON).")
        
        except requests.exceptions.HTTPError as e:
            # Si es un error 4xx (negocio), lo convertimos a nuestra excepción
            # y lo lanzamos. El decorador verá que es 4xx y NO reintentará.
            if 400 <= e.response.status_code < 500:
                raise ErrorNegocio(f"Error HTTP {e.response.status_code}: {e.response.text}")
            
            # Si es 5xx, lo dejamos subir (raise) para que el decorador lo atrape y reintente
            raise e

    # --- MÉTODOS PÚBLICOS (Ya no necesitan decorador porque _request lo tiene) ---

    def listar_productos(self) -> List[Producto]:
        """Obtiene y valida la lista de productos."""
        print("📋 Listando productos...")
        data = self._request("GET", "productos")
        
        if data is None: return [] # Por si acaso

        try:
            return [Producto(**item) for item in data]
        except ValidationError as e:
            raise ErrorValidacion(f"Datos del servidor inválidos: {e}")

    def obtener_producto(self, id_prod: str) -> Optional[Producto]:
        """Obtiene un solo producto validado."""
        print(f"🔍 Buscando ID {id_prod}...")
        # Nota: Asegúrate de pasar str si tu URLBuilder espera str, o int si espera int
        data = self._request("GET", "productos", path_params=[id_prod])
        
        if data is None: # Fue un 404 manejado en _request
            return None
            
        try:
            return Producto(**data)
        except ValidationError as e:
            raise ErrorValidacion(f"El producto {id_prod} tiene formato inválido: {e}")

    def crear_producto(self, datos: dict) -> Producto:
        """Crea un producto."""
        print(f"✨ Creando: {datos.get('nombre')}")
        
        try:
            Producto(**datos) # Validación preliminar
        except ValidationError as e:
            raise ErrorNegocio(f"Datos de entrada inválidos: {e}")

        data = self._request("POST", "productos", data=datos)
        return Producto(**data)

# --- USO ---
if __name__ == "__main__":
    # Esto es solo para probar manualmente si ejecutas el archivo directo
    cliente = EcoMarketClient(RAW_BASE_URL, TOKEN)
    print("--- 🚀 CLIENTE LISTO ---")