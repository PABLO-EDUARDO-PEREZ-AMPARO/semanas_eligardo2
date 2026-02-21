from pydantic import BaseModel, Field, field_validator, PositiveFloat, HttpUrl
from typing import List, Optional
from datetime import datetime

# Reglas de negocio constantes
CATEGORIAS_VALIDAS = {'frutas', 'verduras', 'lacteos', 'miel', 'conservas'}

# Modelo para el objeto anidado (Productor)
class Productor(BaseModel):
    id: str
    nombre: str = Field(..., min_length=2)

# Modelo Principal del Producto
class Producto(BaseModel):
    # Validaciones automáticas de tipos
    id: str
    nombre: str = Field(..., min_length=1, description="El nombre no puede estar vacío")
    
    # PositiveFloat asegura que sea float y > 0
    precio: PositiveFloat 
    
    categoria: str
    
    # Campos opcionales con valores por defecto
    disponible: bool = True
    descripcion: Optional[str] = None
    productor: Optional[Productor] = None
    creado_en: Optional[datetime] = None # Pydantic parsea strings ISO 8601 automáticamente

    # Validación personalizada de lógica de negocio
    @field_validator('categoria')
    @classmethod
    def validar_categoria_negocio(cls, v: str) -> str:
        if v.lower() not in CATEGORIAS_VALIDAS:
            raise ValueError(f"Categoría '{v}' no permitida. Opciones: {CATEGORIAS_VALIDAS}")
        return v.lower()