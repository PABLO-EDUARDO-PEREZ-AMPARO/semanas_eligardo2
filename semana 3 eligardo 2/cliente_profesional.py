import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Optional, List

# --- 1. MODELOS DE DATOS (REFACTORIZACIÓN DE VALIDACIÓN) ---
# Definimos "qué es un producto" y Pydantic se encarga de los if/else.

CATEGORIAS_VALIDAS = {'frutas', 'verduras', 'lacteos', 'miel', 'conservas'}

class ProductoSchema(BaseModel):
    id: int
    nombre: str = Field(..., min_length=1) # Obligatorio, no vacío
    precio: float = Field(..., gt=0)       # Obligatorio, mayor a 0
    categoria: str
    disponible: bool = True
    descripcion: Optional[str] = None
    
    # Validador personalizado para la categoría (Lógica de Negocio)
    @field_validator('categoria')
    @classmethod
    def validar_categoria(cls, v):
        if v not in CATEGORIAS_VALIDAS:
            raise ValueError(f"Categoría '{v}' no permitida. Use: {CATEGORIAS_VALIDAS}")
        return v

# --- 2. EXCEPCIONES PERSONALIZADAS ---
class EcoMarketError(Exception): """Error base"""
class ErrorConexion(EcoMarketError): """Fallo de red o timeout"""
class ErrorNegocio(EcoMarketError): """Datos inválidos o conflictos"""
class RecursoNoEncontrado(EcoMarketError): """404"""

# --- 3. CLASE CLIENTE (REFACTORIZACIÓN DE ESTRUCTURA) ---
class EcoMarketClient:
    
    def __init__(self, base_url: str, token: str, timeout: int = 5):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout_default = timeout
        self.session = self._configurar_sesion_resiliente()

    # --- REFACTORIZACIÓN DE RESILIENCIA (Retries) ---
    def _configurar_sesion_resiliente(self) -> requests.Session:
        session = requests.Session()
        # Definimos la estrategia de reintento
        retry_strategy = Retry(
            total=3,                # Intentar 3 veces
            backoff_factor=1,       # Esperar 1s, 2s, 4s...
            status_forcelist=[500, 502, 503, 504], # Solo en errores de servidor
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"Authorization": f"Bearer {self.token}"})
        return session

    def _request(self, method: str, endpoint: str, data: dict = None, timeout: int = None):
        """Método interno centralizado para manejar todas las peticiones."""
        url = f"{self.base_url}/{endpoint}"
        # Usamos el timeout configurado o el default de la clase
        tiempo_espera = timeout if timeout else self.timeout_default

        try:
            response = self.session.request(
                method=method, 
                url=url, 
                json=data, 
                timeout=tiempo_espera
            )
            response.raise_for_status() # Lanza error si es 4xx o 5xx
            return response
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise RecursoNoEncontrado(f"Recurso no encontrado en {url}")
            elif e.response.status_code == 409:
                raise ErrorNegocio(f"Conflicto: {e.response.text}")
            elif 400 <= e.response.status_code < 500:
                raise ErrorNegocio(f"Error del cliente ({e.response.status_code}): {e.response.text}")
            else:
                raise ErrorConexion(f"Error del servidor: {e}")
        except requests.exceptions.RetryError:
            raise ErrorConexion("Se agotaron los reintentos. El servidor no responde.")
        except requests.exceptions.Timeout:
            raise ErrorConexion("La petición excedió el tiempo límite.")
        except Exception as e:
            raise EcoMarketError(f"Error inesperado: {e}")

    # --- MÉTODOS PÚBLICOS ---

    def listar_productos(self) -> List[ProductoSchema]:
        """Obtiene la lista y la valida contra el esquema automáticamente."""
        print("📋 Listando productos...")
        resp = self._request("GET", "productos")
        raw_data = resp.json()
        
        # AQUÍ OCURRE LA MAGIA DE PYDANTIC
        # Transforma la lista de dicts en una lista de objetos ProductoSchema
        try:
            return [ProductoSchema(**item) for item in raw_data]
        except ValidationError as e:
            raise ErrorNegocio(f"El servidor devolvió datos corruptos: {e}")

    def crear_producto(self, datos: dict) -> ProductoSchema:
        """Valida los datos de entrada ANTES de enviarlos y valida la respuesta."""
        print(f"✨ Creando producto: {datos.get('nombre')}")
        
        # 1. Validamos lo que vamos a enviar (Fail Fast)
        try:
            # Creamos el objeto temporalmente solo para validar
            producto_a_enviar = ProductoSchema(**datos)
        except ValidationError as e:
            raise ErrorNegocio(f"Datos de entrada inválidos: {e}")

        # 2. Enviamos (convertimos el modelo a dict)
        resp = self._request("POST", "productos", data=producto_a_enviar.model_dump())
        
        # 3. Validamos lo que vuelve
        return ProductoSchema(**resp.json())

    def obtener_producto(self, id_p: int) -> Optional[ProductoSchema]:
        print(f"🔍 Buscando ID {id_p}...")
        try:
            resp = self._request("GET", f"productos/{id_p}")
            return ProductoSchema(**resp.json())
        except RecursoNoEncontrado:
            return None

# --- USO DEL CÓDIGO REFACTORIZADO ---
if __name__ == "__main__":
    # Configuración (Simulada)
    URL = os.getenv("ECOMARKET_API_URL", "http://localhost:9999")
    TOKEN = "token_secreto"

    # Instanciamos la clase (Ahora podemos tener varias si queremos)
    cliente = EcoMarketClient(base_url=URL, token=TOKEN, timeout=3)

    print("--- 🚀 INICIANDO CLIENTE PROFESIONAL ---")

    try:
        # 1. Probar Listado
        productos = cliente.listar_productos()
        print(f"✅ Se obtuvieron {len(productos)} productos válidos.")
        for p in productos:
            print(f"   - {p.nombre} (${p.precio}) [{p.categoria}]")

        # 2. Probar Creación (Con datos válidos)
        nuevo = {
            "id": 50,
            "nombre": "Miel Orgánica",
            "precio": 120.50,
            "categoria": "miel",
            "disponible": True
        }
        creado = cliente.crear_producto(nuevo)
        print(f"✅ Producto creado: {creado.nombre}")

        # 3. Probar Error de Validación (Lógica de Negocio)
        print("\n--- 🧪 PROBANDO VALIDACIÓN ---")
        mal_producto = {
            "id": 51,
            "nombre": "Uranio",
            "precio": -50,          # Error: Precio negativo
            "categoria": "nuclear"  # Error: Categoría inválida
        }
        try:
            cliente.crear_producto(mal_producto)
        except ErrorNegocio as e:
            print(f"🛡️ BLOQUEADO CORRECTAMENTE:\n{e}")

    except EcoMarketError as e:
        print(f"❌ Error fatal en la aplicación: {e}")