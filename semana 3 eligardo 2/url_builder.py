from urllib.parse import urlencode, quote, urljoin
import re

class URLBuilder:
    def __init__(self, base_url: str):
        # Aseguramos que la base no tenga barra final para estandarizar la unión
        self.base_url = base_url.rstrip('/')

    def construir(self, endpoint: str, path_params: list = None, query_params: dict = None) -> str:
        """
        Construye una URL segura escapando caracteres y validando tipos.
        
        Args:
            endpoint (str): El recurso base (ej. "productos").
            path_params (list): Lista de IDs o segmentos (ej. [1] o ["frutas", "top"]).
            query_params (dict): Parámetros GET (ej. {"sort": "asc"}).
        """
        # 1. Sanitización del Endpoint base
        # Quitamos barras iniciales/finales para control total
        safe_path = endpoint.strip('/')

        # 2. Procesamiento de Path Params (La parte crítica)
        if path_params:
            for param in path_params:
                # A. Validación de Tipo (Type Safety)
                if not isinstance(param, (int, str)):
                    raise TypeError(f"El parámetro de URL debe ser int o str, recibido: {type(param)}")
                
                # B. Escapado (Sanitización)
                # quote() convierte '/' en '%2F', ' ' en '%20', etc.
                # safe='' asegura que INCLUSO las barras sean escapadas si vienen en el ID.
                param_str = str(param)
                safe_segment = quote(param_str, safe='')
                
                safe_path += f"/{safe_segment}"

        # 3. Unión con la Base
        full_url = f"{self.base_url}/{safe_path}"

        # 4. Construcción de Query String (Parametros GET)
        if query_params:
            # urlencode convierte {'q': 'a&b'} en 'q=a%26b'
            # quote_via=quote asegura espacios como %20 en lugar de +
            query_string = urlencode(query_params, quote_via=quote)
            full_url += f"?{query_string}"

        return full_url