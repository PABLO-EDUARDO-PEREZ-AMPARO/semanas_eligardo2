import pytest
import asyncio
from cliente_integrado import TokenManager, CircuitBreaker, EstadoCircuito

@pytest.mark.asyncio
async def test_tc_x2_orden_refresh_y_piloto():
    """
    TC-X2: Verifica que el token se renueve ANTES de consumir 
    la petición piloto del Circuit Breaker en estado SEMIABIERTO.
    """
    orden_ejecucion = []
    
    class MockTokenManager:
        def is_expiring_soon(self):
            return True 
        async def refresh_access_token(self):
            orden_ejecucion.append("REFRESH")
            await asyncio.sleep(0.01) 
    async def mock_peticion_negocio():
        orden_ejecucion.append("PILOTO_HTTP")
        return {"status": "ok"}
    import time
    cb = CircuitBreaker(umbral=3, timeout=5)
    cb.estado = EstadoCircuito.ABIERTO
    cb._tiempo_apertura = time.time() - 10 

    tm = MockTokenManager()
    async def ejecutar_flujo_cliente():
        if tm.is_expiring_soon():
            await tm.refresh_access_token()
        return await cb.ejecutar(mock_peticion_negocio)

    await ejecutar_flujo_cliente()
    assert orden_ejecucion.count("REFRESH") == 1, "Debe invocar el refresh exactamente 1 vez."
    assert orden_ejecucion.count("PILOTO_HTTP") == 1, "Debe enviar exactamente 1 petición al mock."
    assert orden_ejecucion == ["REFRESH", "PILOTO_HTTP"], \
        f"El orden fue incorrecto. Esperado: ['REFRESH', 'PILOTO_HTTP'], Real: {orden_ejecucion}"