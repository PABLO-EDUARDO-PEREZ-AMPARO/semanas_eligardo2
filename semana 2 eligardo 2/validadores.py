from datetime import datetime

# --- Excepción Personalizada ---
class ValidationError(Exception):
    """Se lanza cuando los datos no cumplen con el esquema esperado."""
    pass

# --- Constantes de Validación ---
CATEGORIAS_VALIDAS = {'frutas', 'verduras', 'lacteos', 'miel', 'conservas'}

def validar_producto(data: dict) -> dict:
    """
    Valida la estructura, tipos y reglas de negocio de un producto.
    Retorna el diccionario si es válido, o lanza ValidationError.
    """
    # 1. Validar que sea un diccionario
    if not isinstance(data, dict):
        raise ValidationError(f"Se esperaba un objeto (dict), se recibió: {type(data).__name__}")

    # 2. Validar Campos Requeridos
    campos_requeridos = {'id', 'nombre', 'precio', 'categoria'}
    campos_faltantes = campos_requeridos - data.keys()
    if campos_faltantes:
        raise ValidationError(f"Faltan campos requeridos: {campos_faltantes}")

    # 3. Validar Tipos de Datos (Type Safety)
    # ID debe ser entero
    if not isinstance(data['id'], int):
        raise ValidationError(f"El campo 'id' debe ser int, recibido: {type(data['id']).__name__}")
    
    # Nombre debe ser string
    if not isinstance(data['nombre'], str):
        raise ValidationError(f"El campo 'nombre' debe ser str, recibido: {type(data['nombre']).__name__}")
    
    # Precio debe ser número (int o float)
    if not isinstance(data['precio'], (int, float)):
        raise ValidationError(f"El campo 'precio' debe ser numérico, recibido: {type(data['precio']).__name__}")
    
    # Disponible (si existe, debe ser bool, aunque el prompt pide validar, asumimos que puede venir)
    if 'disponible' in data and not isinstance(data['disponible'], bool):
         raise ValidationError(f"El campo 'disponible' debe ser bool, recibido: {type(data['disponible']).__name__}")

    # 4. Validar Reglas de Negocio (Logic)
    # Precio positivo
    if data['precio'] <= 0:
        raise ValidationError(f"El precio debe ser mayor a 0. Valor actual: {data['precio']}")
    
    # Categoría permitida
    if data['categoria'] not in CATEGORIAS_VALIDAS:
        raise ValidationError(f"Categoría '{data['categoria']}' inválida. Permitidas: {CATEGORIAS_VALIDAS}")

    # 5. Validar Campos Opcionales (si existen)
    
    # Descripción
    if 'descripcion' in data and not isinstance(data['descripcion'], str):
        raise ValidationError("El campo 'descripcion' debe ser texto (str).")

    # Productor (Debe ser dict con id y nombre)
    if 'productor' in data:
        prod = data['productor']
        if not isinstance(prod, dict):
            raise ValidationError("El campo 'productor' debe ser un objeto (dict).")
        if 'id' not in prod or 'nombre' not in prod:
            raise ValidationError("El 'productor' debe tener 'id' y 'nombre'.")

    # Creado_en (Formato ISO 8601)
    if 'creado_en' in data:
        if not isinstance(data['creado_en'], str):
             raise ValidationError("El campo 'creado_en' debe ser un string.")
        try:
            # Intentamos parsear para verificar que sea una fecha válida
            # replace('Z', '+00:00') ayuda a que Python < 3.11 entienda la Z de UTC
            datetime.fromisoformat(data['creado_en'].replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError(f"El campo 'creado_en' no es una fecha ISO 8601 válida: {data['creado_en']}")

    return data

def validar_lista_productos(data: list) -> list:
    """
    Valida que la entrada sea una lista y que cada elemento sea un producto válido.
    """
    if not isinstance(data, list):
        raise ValidationError(f"Se esperaba una lista de productos, se recibió: {type(data).__name__}")
    
    lista_validada = []
    for indice, item in enumerate(data):
        try:
            # Reutilizamos la lógica de validación individual
            producto_valido = validar_producto(item)
            lista_validada.append(producto_valido)
        except ValidationError as e:
            # Enriquecemos el error indicando en qué índice falló
            raise ValidationError(f"Error en el producto índice {indice}: {str(e)}")
            
    return lista_validada