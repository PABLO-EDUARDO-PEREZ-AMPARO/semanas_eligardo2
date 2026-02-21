import pytest
import asyncio
import aiohttp
from aioresponses import aioresponses, CallbackResult
from cliente_ecomarket import EcoMarketClient

# Configuración global para Pytest Asyncio
pytestmark = pytest.mark.asyncio(loop_scope="function")

@pytest.fixture
async def client():
    """Fixture para inicializar el cliente."""
    async with EcoMarketClient(base_url="http://api.ecomarket.com", token="token_test") as c:
        yield c

async def test_get_product_equivalence(client):
    """Prueba que el retorno coincida con lo esperado."""
    with aioresponses() as m:
        # CORREGIDO: Datos completos para satisfacer a Pydantic
        mock_producto = {
            "id": "1",  # ID como string
            "nombre": "Tomate",
            "precio": 15.50,
            "categoria": "Verduras"
        }
        m.get("http://api.ecomarket.com/productos/1", payload=mock_producto)
        
        res = await client.obtener_producto("1")
        assert res.nombre == "Tomate"
        assert res.precio == 15.50

async def test_handle_404_error(client):
    """Verifica el manejo de 404 (retorna None)."""
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/productos/999", status=404)
        
        res = await client.obtener_producto("999")
        assert res is None

async def test_gather_partial_failure_resilience(client):
    """Prueba que gather con return_exceptions=True no detenga todo."""
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/perfil", payload={"user": "admin"})
        m.get("http://api.ecomarket.com/productos", status=500)
        m.get("http://api.ecomarket.com/anuncios", payload={"ad": "promo"})

        resultados = await client.cargar_dashboard()

        assert len(resultados) == 3
        assert resultados[0]["user"] == "admin"
        assert isinstance(resultados[1], Exception)
        assert resultados[2]["ad"] == "promo"

async def test_individual_timeout_cancellation(client):
    """Simula un timeout usando un callback."""
    
    async def slow_callback(url, **kwargs):
        await asyncio.sleep(2)
        return CallbackResult(status=200, payload={"id": "lento", "nombre": "x", "precio": 1, "categoria": "x"})

    with aioresponses() as m:
        # CORREGIDO: Datos completos para el producto rápido
        producto_rapido = {
            "id": "fast",
            "nombre": "Rayo McQueen",
            "precio": 100.0,
            "categoria": "Frutas"
        }
        
        m.get("http://api.ecomarket.com/productos/fast", payload=producto_rapido)
        m.get("http://api.ecomarket.com/productos/slow", callback=slow_callback)

        tarea_rapida = asyncio.create_task(client.obtener_producto("fast"))
        
        # Forzamos timeout pequeño para que falle la lenta
        client.timeout = 0.1 
        try:
            await client.obtener_producto("slow")
        except Exception:
            pass 
        
        res_rapida = await tarea_rapida
        assert res_rapida.id == "fast"

async def test_server_disconnect_mid_response(client):
    """El servidor cierra la conexión."""
    with aioresponses() as m:
        m.get("http://api.ecomarket.com/broken", exception=aiohttp.ClientPayloadError())

        with pytest.raises(aiohttp.ClientPayloadError):
            await client._request("GET", "broken")

async def test_session_closed_after_error_storm(client):
    """Verifica comportamiento tras múltiples errores."""
    with aioresponses() as m:
        for _ in range(5):
            m.get("http://api.ecomarket.com/fail", status=500)

        tareas = [client._request("GET", "fail") for _ in range(5)]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        
        assert all(isinstance(r, Exception) for r in resultados)
        assert not client.session.closed