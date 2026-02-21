import timeit
import json
from pydantic import BaseModel, PositiveFloat, Field, ValidationError as PydanticError
from jsonschema import validate, ValidationError as SchemaError
from typing import List, Optional

# --- DATOS DE PRUEBA (Un producto típico de EcoMarket) ---
dato_valido = {
    "id": 1,
    "nombre": "Miel Orgánica de Abeja",
    "precio": 150.50,
    "tags": ["orgánico", "dulces", "oferta"],
    "productor": {
        "id": 99,
        "nombre": "Granja La Esperanza"
    }
}

# ==========================================
# ESTRATEGIA 1: VALIDACIÓN MANUAL (Tu código actual)
# ==========================================
def validar_manual(data):
    # 1. Validar estructura base
    if not isinstance(data, dict):
        raise ValueError("Debe ser un diccionario")
    
    # 2. Validar ID
    if "id" not in data or not isinstance(data["id"], int):
        raise ValueError("Falta ID o no es entero")
        
    # 3. Validar Nombre
    if "nombre" not in data or not isinstance(data["nombre"], str):
        raise ValueError("Falta nombre o no es string")
        
    # 4. Validar Precio
    if "precio" not in data or not isinstance(data["precio"], (int, float)):
        raise ValueError("Falta precio o no es numérico")
    if data["precio"] <= 0:
        raise ValueError("Precio debe ser positivo")
        
    # 5. Validar Productor (Anidado)
    if "productor" in data:
        prod = data["productor"]
        if not isinstance(prod, dict):
            raise ValueError("Productor inválido")
        if "id" not in prod or not isinstance(prod["id"], int):
            raise ValueError("ID de productor inválido")
            
    return True

# ==========================================
# ESTRATEGIA 2: PYDANTIC V2 (Recomendado)
# ==========================================
class ProductorModel(BaseModel):
    id: int
    nombre: str

class ProductoModel(BaseModel):
    id: int
    nombre: str
    precio: PositiveFloat
    tags: List[str] = []
    productor: Optional[ProductorModel] = None

def validar_pydantic(data):
    try:
        # Pydantic parsea y valida al instanciar
        ProductoModel(**data)
        return True
    except PydanticError:
        return False

# ==========================================
# ESTRATEGIA 3: JSON SCHEMA
# ==========================================
schema_producto = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "nombre": {"type": "string"},
        "precio": {"type": "number", "exclusiveMinimum": 0},
        "tags": {"type": "array", "items": {"type": "string"}},
        "productor": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "nombre": {"type": "string"}
            },
            "required": ["id"]
        }
    },
    "required": ["id", "nombre", "precio"]
}

def validar_jsonschema(data):
    try:
        validate(instance=data, schema=schema_producto)
        return True
    except SchemaError:
        return False

# ==========================================
# BENCHMARK (PRUEBA DE RENDIMIENTO)
# ==========================================
if __name__ == "__main__":
    print("--- 🏁 INICIANDO BENCHMARK (100,000 iteraciones) ---")
    
    iteraciones = 100000
    
    # 1. Medir Manual
    tiempo_manual = timeit.timeit(lambda: validar_manual(dato_valido), number=iteraciones)
    print(f"1. Manual (If/Else): {tiempo_manual:.4f} segundos")
    
    # 2. Medir Pydantic
    tiempo_pydantic = timeit.timeit(lambda: validar_pydantic(dato_valido), number=iteraciones)
    print(f"2. Pydantic v2:      {tiempo_pydantic:.4f} segundos")
    
    # 3. Medir JSON Schema
    tiempo_schema = timeit.timeit(lambda: validar_jsonschema(dato_valido), number=iteraciones)
    print(f"3. JSON Schema:      {tiempo_schema:.4f} segundos")
    
    print("\n--- 📊 ANÁLISIS ---")
    print(f"Pydantic es {tiempo_schema / tiempo_pydantic:.1f}x más rápido que JSON Schema")
    print(f"Validación manual es la más rápida, pero la más difícil de mantener.")