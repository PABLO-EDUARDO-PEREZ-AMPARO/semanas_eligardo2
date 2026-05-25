import pytest
import asyncio
import time
from cliente_integrado import CircuitBreaker, EstadoCircuito

@pytest.mark.asyncio
async def test_inv_a2_concurrencia_semiabierto():
    """
    INV-A2: En estado SEMIABIERTO, solo 1 petición debe intentar tocar la red.
    Si lanzamos 3 simultáneas, 1 pasa al mock, las otras 2 lanzan CircuitOpenError.
    """
    cb = CircuitBreaker(umbral=1, timeout=0.1)
    cb.estado = EstadoCircuito.ABIERTO
    cb._tiempo_apertura = time.time() - 0.2 
    peticiones_a_red = 0
    
    async def mock_peticion_http():
        nonlocal peticiones_a_red
        peticiones_a_red += 1
        await asyncio.sleep(0.1) 
    tareas = [
        asyncio.create_task(cb.ejecutar(mock_peticion_http)),
        asyncio.create_task(cb.ejecutar(mock_peticion_http)),
        asyncio.create_task(cb.ejecutar(mock_peticion_http))
    ]
    resultados = await asyncio.gather(*tareas, return_exceptions=True)
    assert peticiones_a_red == 1, f"¡Thundering Herd detectado! Pasaron {peticiones_a_red} peticiones."
    errores_bloqueados = sum(1 for r in resultados if isinstance(r, Exception) and 'CircuitOpenError' in str(r))
    assert errores_bloqueados == 2, f"Debieron bloquearse 2 peticiones, pero se bloquearon {errores_bloqueados}"