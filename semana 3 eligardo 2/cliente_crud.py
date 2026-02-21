import requests
import os
import json

# --- CONFIGURACIÓN Y EXCEPCIONES ---
BASE_URL = os.getenv("ECOMARKET_API_URL", "http://localhost:9999")
TIMEOUT = 5

class EcoMarketError(Exception): """Error base del cliente"""
class RecursoNoEncontrado(EcoMarketError): """404 Not Found"""
class ConflictoDatos(EcoMarketError): """409 Conflict"""
class ErrorServidor(EcoMarketError): """500 Internal Error"""

# --- FUNCIONES CRUD SOLICITADAS ---

def crear_producto(datos: dict) -> dict:
    """
    Crea un nuevo producto en el servidor.
    
    Args:
        datos (dict): Diccionario con nombre, precio, stock, etc.
        
    Returns:
        dict: El producto creado incluyendo su ID asignado.
        
    Raises:
        ConflictoDatos: Si el producto ya existe (409).
        EcoMarketError: Para otros errores HTTP.
        
    Ejemplo:
        >>> p = crear_producto({"nombre": "Miel", "precio": 100})
        >>> print(p['id'])
    """
    url = f"{BASE_URL}/productos"
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=datos, headers=headers, timeout=TIMEOUT)
    
    if response.status_code == 201:
        return response.json()
    elif response.status_code == 409:
        raise ConflictoDatos(f"El producto ya existe: {response.text}")
    else:
        response.raise_for_status() # Lanza error genérico de requests
        return {} # Fallback

def actualizar_producto_total(producto_id: int, datos: dict) -> dict:
    """
    Reemplaza COMPLETAMENTE un producto existente (PUT).
    
    ⚠️ CUIDADO: Los campos no incluidos en 'datos' serán borrados.
    
    Args:
        producto_id (int): ID del recurso.
        datos (dict): Objeto completo del producto.
        
    Returns:
        dict: El producto actualizado.
    """
    url = f"{BASE_URL}/productos/{producto_id}"
    headers = {"Content-Type": "application/json"}
    
    response = requests.put(url, json=datos, headers=headers, timeout=TIMEOUT)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise RecursoNoEncontrado(f"No se puede actualizar: ID {producto_id} no existe.")
    else:
        response.raise_for_status()
        return {}

def actualizar_producto_parcial(producto_id: int, campos: dict) -> dict:
    """
    Modifica SOLO los campos enviados (PATCH).
    
    Args:
        producto_id (int): ID del recurso.
        campos (dict): Diccionario con los valores a cambiar (ej. solo precio).
        
    Returns:
        dict: El producto con los cambios aplicados.
    """
    url = f"{BASE_URL}/productos/{producto_id}"
    headers = {"Content-Type": "application/json"}
    
    response = requests.patch(url, json=campos, headers=headers, timeout=TIMEOUT)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise RecursoNoEncontrado(f"No se puede parchear: ID {producto_id} no existe.")
    else:
        response.raise_for_status()
        return {}

def eliminar_producto(producto_id: int) -> bool:
    """
    Elimina un producto del sistema.
    
    Args:
        producto_id (int): ID del producto a borrar.
        
    Returns:
        bool: True si se eliminó correctamente.
        
    Raises:
        RecursoNoEncontrado: Si el ID no existe (404).
    """
    url = f"{BASE_URL}/productos/{producto_id}"
    
    response = requests.delete(url, timeout=TIMEOUT)
    
    if response.status_code == 204:
        return True
    elif response.status_code == 404:
        raise RecursoNoEncontrado(f"Error al borrar: El producto {producto_id} no existe.")
    else:
        response.raise_for_status()
        return False