import asyncio
import aiohttp
from typing import List, Optional, Any
from pydantic import ValidationError
from modelos import Producto
from url_builder import URLBuilder
import json # Necesario para capturar JSONDecodeError

# --- EXCEPCIONES PERSONALIZADAS ---
class EcoMarketError(Exception): 
    """Error base de la aplicación."""
    pass

class ErrorValidacion(EcoMarketError): 
    """Los datos no cumplen con el esquema esperado."""
    pass

class ErrorNegocio(EcoMarketError): 
    """Errores lógicos o respuestas 4xx/5xx del servidor."""
    pass

class EcoMarketClient:
    def __init__(self, base_url: str, token: str, timeout: float = 5.0): # Timeout como float
        self.url_tool = URLBuilder(base_url)
        self.token = token
        self.timeout = aiohttp.ClientTimeout(total=timeout) # Objeto Timeout correcto de aiohttp
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.session = None

    async def __aenter__(self):
        # Pasamos el timeout a la sesión globalmente
        self.session = aiohttp.ClientSession(headers=self.headers, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, path_params: list = None, data: dict = None) -> Any:
        url = self.url_tool.construir(endpoint, path_params=path_params)
        
        if self.session is None:
            raise EcoMarketError("La sesión no está iniciada. Usa 'async with'.")

        try:
            # NO pasamos timeout aquí para que use el de la sesión (que podemos modificar en tests)
            # Ojo: si modificas self.session.timeout en el test, afectará aquí.
            async with self.session.request(method=method, url=url, json=data) as response:
                
                if response.status == 404:
                    return None
                
                if response.status >= 400:
                    text = await response.text()
                    raise ErrorNegocio(f"Error HTTP {response.status}: {text}")

                if response.status == 204:
                    return {}

                try:
                    return await response.json()
                except (aiohttp.ContentTypeError, json.JSONDecodeError, ValueError):
                    # Capturamos TODO error de parseo JSON
                    raise EcoMarketError("El servidor no devolvió un JSON válido.")

        except asyncio.TimeoutError:
            raise EcoMarketError("El servidor tardó demasiado en responder (Timeout).")
        except aiohttp.ClientError as e:
            raise e 

    # --- MÉTODOS PÚBLICOS ---

    async def obtener_producto(self, id_prod: str) -> Optional[Producto]:
        data = await self._request("GET", "productos", path_params=[id_prod])
        if data is None:
            return None
        try:
            return Producto(**data)
        except ValidationError as e:
            raise ErrorValidacion(f"Datos inválidos al obtener producto: {e}")

    async def crear_producto(self, datos: dict) -> Producto:
        try:
            prod_temp = Producto(**{**datos, "id": "temp"}) 
        except ValidationError as e:
            raise ErrorNegocio(f"Datos de entrada inválidos: {e}")

        data = await self._request("POST", "productos", data=datos)
        return Producto(**data)

    async def cargar_dashboard(self):
        tareas = [
            self._request("GET", "perfil"),
            self._request("GET", "productos"),
            self._request("GET", "anuncios")
        ]
        return await asyncio.gather(*tareas, return_exceptions=True)