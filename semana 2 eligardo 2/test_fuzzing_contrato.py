import pytest
import yaml
import responses
from hypothesis import given, settings, strategies as st
from hypothesis_jsonschema import from_schema
from cliente_ecomarket import EcoMarketClient

# 1. Cargar definición OpenAPI
with open("openapi.yaml", "r", encoding="utf-8") as f:
    openapi_spec = yaml.safe_load(f)

# 2. Extraer manualmente el esquema para evitar librerías externas fallidas
# Accedemos directo al diccionario del YAML
schema_raw = openapi_spec['components']['schemas']['Producto']

# 3. Adaptación para Hypothesis
# Hypothesis necesita un esquema "autocontenido". 
# Como el YAML es simple, usamos el diccionario directo.
schema_producto_test = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},  # Tu YAML dice string, asegúrate que tu Pydantic sea string
        "nombre": {"type": "string", "minLength": 1},
        "precio": {"type": "number", "minimum": 0.1},
        "stock": {"type": "integer", "minimum": 0},
        "categoria": {"type": "string"}
    },
    "required": ["id", "nombre", "precio"]
}

schema_lista_productos = {
    "type": "array",
    "items": schema_producto_test
}

class TestContractFuzzing:
    
    @pytest.fixture
    def cliente(self):
        # Usamos un token dummy y URL base
        return EcoMarketClient("http://api-mock", "token_test")

    # ----------------------------------------------------------------
    # TEST 1: FUZZING DE LISTADO (GET /productos)
    # Genera listas aleatorias válidas y verifica que el cliente las procese
    # ----------------------------------------------------------------
    @settings(max_examples=30) # Probamos 30 variantes locas
    @given(payload=from_schema(schema_lista_productos))
    @responses.activate
    def test_fuzzing_listar_productos(self, cliente, payload):
        # 1. Mockeamos el servidor devolviendo la "basura válida" generada
        responses.add(
            responses.GET,
            "http://api-mock/productos",
            json=payload,
            status=200
        )
        
        # 2. Ejecutamos el cliente
        try:
            resultados = cliente.listar_productos()
            
            # 3. Verificamos que Pydantic no explotó
            assert len(resultados) == len(payload)
            print(f"✅ Test pasado con {len(payload)} items generados.")
                
        except Exception as e:
            # Si entra aquí, es porque generamos un JSON que el contrato permite
            # pero tu Cliente (Pydantic) rechazó. ¡Eso es un bug de contrato!
            pytest.fail(f"CRASH: El cliente falló con datos válidos del esquema: {e}")

    # ----------------------------------------------------------------
    # TEST 2: FUZZING DE UN PRODUCTO (GET /productos/{id})
    # ----------------------------------------------------------------
    @settings(max_examples=30)
    @given(payload=from_schema(schema_producto_test))
    @responses.activate
    def test_fuzzing_obtener_producto(self, cliente, payload):
        # Simulamos que buscamos el ID generado
        fake_id = payload.get("id", "1")
        
        responses.add(
            responses.GET,
            f"http://api-mock/productos/{fake_id}",
            json=payload,
            status=200
        )
        
        try:
            prod = cliente.obtener_producto(fake_id)
            assert prod is not None
            # Verificamos integridad básica
            assert prod.nombre == payload['nombre']
        except Exception as e:
            pytest.fail(f"CRASH al obtener producto individual: {e}\nPayload: {payload}")