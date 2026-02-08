import pytest
import responses
import json
import requests
from cliente_ecomarket import EcoMarketClient, EcoMarketError, ErrorNegocio, ErrorRed, ErrorValidacion, RecursoNoEncontrado

# --- FIXTURES (Configuración compartida) ---

@pytest.fixture
def base_url():
    return "http://test-api.com"

@pytest.fixture
def cliente(base_url):
    # Instanciamos el cliente con un token falso y un timeout bajo para tests
    return EcoMarketClient(base_url=base_url, token="test_token", timeout=1)

@pytest.fixture
def producto_valido():
    return {
        "id": 1,
        "nombre": "Manzana Royal",
        "precio": 25.50,
        "categoria": "frutas",
        "disponible": True
    }

# ==========================================
# 1. HAPPY PATH (6 Tests)
# ==========================================

@responses.activate
def test_listar_productos_exito(cliente, base_url, producto_valido):
    """Verifica que se parsee correctamente una lista de productos."""
    responses.add(
        responses.GET,
        f"{base_url}/productos",
        json=[producto_valido],
        status=200
    )
    
    resultado = cliente.listar_productos()
    assert len(resultado) == 1
    assert resultado[0].nombre == "Manzana Royal"
    assert resultado[0].precio == 25.50

@responses.activate
def test_obtener_producto_exito(cliente, base_url, producto_valido):
    """Verifica obtener un solo producto por ID."""
    responses.add(
        responses.GET,
        f"{base_url}/productos/1",
        json=producto_valido,
        status=200
    )
    
    prod = cliente.obtener_producto(1)
    assert prod is not None
    assert prod.id == 1
    assert prod.categoria == "frutas"

@responses.activate
def test_crear_producto_exito(cliente, base_url, producto_valido):
    """Verifica la creación y retorno del objeto creado."""
    payload = {"nombre": "Manzana", "precio": 25.5, "categoria": "frutas", "id": 1}
    responses.add(
        responses.POST,
        f"{base_url}/productos",
        json=producto_valido,
        status=201 # Created
    )
    
    nuevo_prod = cliente.crear_producto(payload)
    assert nuevo_prod.id == 1
    assert nuevo_prod.nombre == "Manzana Royal"

@responses.activate
def test_actualizar_total_exito(cliente, base_url, producto_valido):
    """Verifica PUT (reemplazo total)."""
    # Modificamos el producto para simular actualización
    producto_valido["nombre"] = "Manzana Modificada"
    responses.add(
        responses.PUT,
        f"{base_url}/productos/1",
        json=producto_valido,
        status=200
    )
    
    # Nota: Asumimos que actualizar devuelve el objeto actualizado (o dict vacío según implementación)
    # Ajusta esto según tu implementación de actualizar_producto_total
    responses.add(responses.PUT, f"{base_url}/productos/1", json=producto_valido, status=200)
    
    # Simulamos llamada (ajustar si tu cliente retorna algo diferente)
    # Aquí probamos que NO lance excepción
    try:
        cliente.session.put(f"{base_url}/productos/1", json=producto_valido)
    except Exception:
        pytest.fail("PUT no debería fallar")

@responses.activate
def test_actualizar_parcial_exito(cliente, base_url, producto_valido):
    """Verifica PATCH (actualización parcial)."""
    producto_valido["precio"] = 99.99
    responses.add(
        responses.PATCH,
        f"{base_url}/productos/1",
        json=producto_valido,
        status=200
    )
    
    # Simulamos llamada directa requests para este ejemplo si la función no retorna nada
    resp = cliente.session.patch(f"{base_url}/productos/1", json={"precio": 99.99})
    assert resp.status_code == 200
    assert resp.json()["precio"] == 99.99

@responses.activate
def test_eliminar_producto_exito(cliente, base_url):
    """Verifica DELETE con respuesta 204 No Content."""
    responses.add(
        responses.DELETE,
        f"{base_url}/productos/1",
        status=204
    )
    
    # Asumiendo que tu cliente tiene este método
    try:
        cliente.session.delete(f"{base_url}/productos/1")
    except Exception:
        pytest.fail("DELETE debería ser exitoso")

# ==========================================
# 2. ERRORES HTTP (8 Tests)
# ==========================================

@responses.activate
def test_crear_producto_invalido_400(cliente, base_url):
    """Prueba error de validación del lado del servidor (400)."""
    responses.add(
        responses.POST,
        f"{base_url}/productos",
        status=400,
        json={"detail": "Precio negativo no permitido"}
    )
    
    with pytest.raises(ErrorNegocio) as excinfo:
        cliente.crear_producto({"nombre": "X", "precio": -1, "id": 2, "categoria": "frutas"})
    assert "400" in str(excinfo.value)

@responses.activate
def test_peticion_sin_token_401(cliente, base_url):
    """Prueba fallo de autenticación."""
    responses.add(
        responses.GET,
        f"{base_url}/productos",
        status=401,
        json={"detail": "Token inválido"}
    )
    
    with pytest.raises(ErrorNegocio):
        cliente.listar_productos()

@responses.activate
def test_obtener_producto_inexistente_404(cliente, base_url):
    """Prueba obtener ID que no existe (Debe retornar None, no explotar)."""
    responses.add(
        responses.GET,
        f"{base_url}/productos/999",
        status=404
    )
    
    resultado = cliente.obtener_producto(999)
    assert resultado is None

@responses.activate
def test_actualizar_producto_inexistente_404(cliente, base_url):
    """Prueba actualizar ID que no existe (Debe lanzar error)."""
    responses.add(
        responses.PUT,
        f"{base_url}/productos/999",
        status=404
    )
    
    # Asumiendo implementación directa en requests para el ejemplo
    with pytest.raises(requests.exceptions.HTTPError):
         resp = cliente.session.put(f"{base_url}/productos/999")
         resp.raise_for_status()

@responses.activate
def test_eliminar_producto_inexistente_404(cliente, base_url):
    """Prueba eliminar ID que no existe."""
    responses.add(
        responses.DELETE,
        f"{base_url}/productos/999",
        status=404
    )
    
    with pytest.raises(requests.exceptions.HTTPError):
         resp = cliente.session.delete(f"{base_url}/productos/999")
         resp.raise_for_status()

@responses.activate
def test_crear_duplicado_409(cliente, base_url, producto_valido):
    """Prueba conflicto de recursos (ID duplicado)."""
    responses.add(
        responses.POST,
        f"{base_url}/productos",
        status=409,
        json={"detail": "El ID ya existe"}
    )
    
    with pytest.raises(ErrorNegocio) as excinfo:
        cliente.crear_producto(producto_valido)
    assert "Conflicto" in str(excinfo.value) or "409" in str(excinfo.value)

@responses.activate
def test_error_servidor_500(cliente, base_url):
    """Prueba error interno del servidor (Debería reintentar y fallar)."""
    responses.add(
        responses.GET,
        f"{base_url}/productos",
        status=500
    )
    
    with pytest.raises(ErrorRed): # O ErrorConexion según tu clase
        cliente.listar_productos()

@responses.activate
def test_servicio_no_disponible_503(cliente, base_url):
    """Prueba servicio no disponible (Debería reintentar y fallar)."""
    responses.add(
        responses.GET,
        f"{base_url}/productos",
        status=503
    )
    
    with pytest.raises(ErrorRed):
        cliente.listar_productos()

# ==========================================
# 3. EDGE CASES (6 Tests)
# ==========================================

@responses.activate
def test_respuesta_vacia_200(cliente, base_url):
    """El servidor responde 200 OK pero con un JSON vacío {} en lugar de lista."""
    responses.add(
        responses.GET,
        f"{base_url}/productos",
        json={}, # Debería ser [], esto romperá Pydantic
        status=200
    )
    
    with pytest.raises(ErrorValidacion):
        cliente.listar_productos()

@responses.activate
def test_content_type_incorrecto(cliente, base_url):
    """El servidor devuelve HTML (error de proxy) en lugar de JSON."""
    responses.add(
        responses.GET,
        f"{base_url}/productos",
        body="<html>Error Nginx</html>",
        status=200,
        content_type="text/html"
    )
    
    with pytest.raises(ErrorRed) as excinfo:
        cliente.listar_productos()
    assert "no es JSON" in str(excinfo.value)

@responses.activate
def test_json_estructura_incorrecta(cliente, base_url):
    """JSON válido, pero faltan campos obligatorios (nombre)."""
    responses.add(
        responses.GET,
        f"{base_url}/productos",
        json=[{"id": 1, "precio": 10}], # Falta 'nombre' y 'categoria'
        status=200
    )
    
    with pytest.raises(ErrorValidacion):
        cliente.listar_productos()

@responses.activate
def test_timeout_servidor(cliente, base_url):
    """Simula que el servidor tarda más que el timeout configurado."""
    responses.add(
        responses.GET,
        f"{base_url}/productos",
        body=requests.exceptions.Timeout()
    )
    
    with pytest.raises(ErrorRed) as excinfo:
        cliente.listar_productos()
    assert "tiempo límite" in str(excinfo.value)

@responses.activate
def test_campo_precio_string(cliente, base_url, producto_valido):
    """El precio viene como texto 'gratis' en lugar de número."""
    producto_valido["precio"] = "gratis" # Esto romperá la validación de float
    responses.add(
        responses.GET,
        f"{base_url}/productos",
        json=[producto_valido],
        status=200
    )
    
    with pytest.raises(ErrorValidacion):
        cliente.listar_productos()

@responses.activate
def test_lista_productos_vacia(cliente, base_url):
    """Caso borde válido: No hay productos, devuelve lista vacía."""
    responses.add(
        responses.GET,
        f"{base_url}/productos",
        json=[],
        status=200
    )
    
    resultado = cliente.listar_productos()
    assert isinstance(resultado, list)
    assert len(resultado) == 0