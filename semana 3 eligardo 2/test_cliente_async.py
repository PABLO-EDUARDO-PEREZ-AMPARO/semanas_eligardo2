import pytest
import asyncio
import aiohttp
from aioresponses import aioresponses, CallbackResult
# Asegúrate de importar las excepciones desde tu cliente
from cliente_ecomarket import EcoMarketClient, ErrorNegocio, ErrorValidacion, EcoMarketError

pytestmark = pytest.mark.asyncio(loop_scope="function")

PRODUCTO_VALIDO = {"id": "1", "nombre": "Manzana", "precio": 10.0, "categoria": "Frutas"}
PRODUCTO_NUEVO = {"nombre": "Pera", "precio": 12.0, "categoria": "Frutas"}

@pytest.fixture
async def client():
    async with EcoMarketClient(base_url="http://api.ecomarket.com", token="token_test") as c:
        yield c

# --- TESTS ---

async def test_obtener_producto_exito(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/1", payload=PRODUCTO_VALIDO)
        res = await client.obtener_producto("1")
        assert res.nombre == "Manzana"

async def test_obtener_producto_404(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/999", status=404)
        res = await client.obtener_producto("999")
        assert res is None

async def test_crear_producto_exito(client):
    with aioresponses() as m:
        resp_data = {**PRODUCTO_NUEVO, "id": "2"}
        m.post("http://api.ecomarket.com/productos", payload=resp_data, status=201)
        res = await client.crear_producto(PRODUCTO_NUEVO)
        assert res.id == "2"

async def test_crear_producto_validacion_cliente(client):
    datos_malos = {"nombre": "Incompleto"} 
    with pytest.raises(ErrorNegocio):
        await client.crear_producto(datos_malos)

async def test_error_400_bad_request(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/x", status=400, body="ID inválido")
        with pytest.raises(ErrorNegocio) as exc:
            await client.obtener_producto("x")
        assert "400" in str(exc.value)

async def test_error_500_server_error(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/1", status=500)
        with pytest.raises(ErrorNegocio) as exc:
            await client.obtener_producto("1")
        assert "500" in str(exc.value)

async def test_timeout_error(client):
    """
    Simula un Timeout forzando la excepción directamente.
    Esta es la forma más robusta de probar que el cliente captura el error.
    """
    with aioresponses() as m:
        # Forzamos a que la petición falle con asyncio.TimeoutError
        m.get("http://api.ecomarket.com/productos/1", exception=asyncio.TimeoutError())
        
        with pytest.raises(EcoMarketError) as exc:
            await client.obtener_producto("1")
        
        # Verificamos que el mensaje sea el que definimos en cliente_ecomarket.py
        assert "Timeout" in str(exc.value) or "tardó demasiado" in str(exc.value)

async def test_respuesta_no_json(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/1", status=200, body="<html>Error</html>", content_type="text/html")
        with pytest.raises(EcoMarketError) as exc: 
            await client.obtener_producto("1")
        assert "JSON válido" in str(exc.value)

async def test_dashboard_exito_total(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/perfil", payload={"user": "admin"})
        m.get("http://api.ecomarket.com/productos", payload=[])
        m.get("http://api.ecomarket.com/anuncios", payload=[])
        res = await client.cargar_dashboard()
        assert len(res) == 3
        assert not any(isinstance(r, Exception) for r in res)

async def test_dashboard_parcial(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/perfil", payload={"user": "admin"})
        m.get("http://api.ecomarket.com/productos", status=500)
        m.get("http://api.ecomarket.com/anuncios", payload=[])
        res = await client.cargar_dashboard()
        assert isinstance(res[1], Exception)
        assert res[0]["user"] == "admin"

async def test_validacion_pydantic_respuesta(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/1", payload={"id": "1", "nombre": "Invalido"})
        with pytest.raises(ErrorValidacion):
            await client.obtener_producto("1")

async def test_categoria_invalida_respuesta(client):
    with aioresponses() as m:
        prod = {**PRODUCTO_VALIDO, "categoria": "Coches"}
        m.get("http://api.ecomarket.com/productos/1", payload=prod)
        with pytest.raises(ErrorValidacion):
            await client.obtener_producto("1")

async def test_session_lifecycle(client):
    assert not client.session.closed

# --- TESTS ADICIONALES PARA LLEGAR A 20+ ---

async def test_error_401(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/1", status=401)
        with pytest.raises(ErrorNegocio): await client.obtener_producto("1")

async def test_error_403(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/1", status=403)
        with pytest.raises(ErrorNegocio): await client.obtener_producto("1")

async def test_error_502(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/1", status=502)
        with pytest.raises(ErrorNegocio): await client.obtener_producto("1")

async def test_error_503(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/1", status=503)
        with pytest.raises(ErrorNegocio): await client.obtener_producto("1")

async def test_error_504(client):
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/1", status=504)
        with pytest.raises(ErrorNegocio): await client.obtener_producto("1")

async def test_request_204_no_content(client):
    """Verifica respuesta vacía."""
    with aioresponses() as m:
        m.delete("http://api.ecomarket.com/productos/1", status=204)
        res = await client._request("DELETE", "productos/1")
        assert res == {}

async def test_post_json_corrupto(client):
    """Simula JSON roto en respuesta a un POST."""
    with aioresponses() as m:
        m.post("http://api.ecomarket.com/productos", body="{", content_type="application/json")
        with pytest.raises(EcoMarketError):
            await client.crear_producto(PRODUCTO_NUEVO)

async def test_headers_auth(client):
    assert client.session._default_headers["Authorization"] == "Bearer token_test"

async def test_listar_varios_elementos(client):
    # Simulación simple de lista
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos", payload=[PRODUCTO_VALIDO, PRODUCTO_VALIDO])
        res = await client._request("GET", "productos")
        assert len(res) == 2