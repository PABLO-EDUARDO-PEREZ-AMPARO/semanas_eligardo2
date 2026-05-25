import time
from enum import Enum

class EstadoCircuito(Enum):
    CERRADO = "CERRADO"
    ABIERTO = "ABIERTO"
    SEMIABIERTO = "SEMIABIERTO"

class CircuitBreaker:
    def __init__(self, umbral=3, timeout=5):
        self.umbral = umbral
        self.timeout = timeout
        self.estado = EstadoCircuito.CERRADO
        self.fallos = 0
        self._tiempo_apertura = 0

    async def ejecutar(self, fn):
        if self.estado == EstadoCircuito.ABIERTO:
            if time.time() - self._tiempo_apertura >= self.timeout:
                print("🟡 [CB] Tiempo de gracia finalizado. Transición a SEMIABIERTO (Piloto)")
                self.estado = EstadoCircuito.SEMIABIERTO
            else:
                raise Exception("CircuitOpenError (Fallo rápido - protegiendo el sistema)")
        elif self.estado == EstadoCircuito.SEMIABIERTO:
            raise Exception("CircuitOpenError (Fallo rápido - Piloto ya en vuelo)")

        try:
            resultado = await fn()
            self._on_exito()
            return resultado
        except Exception as e:
            # Filtrado inteligente: los errores 401 de autenticación no deben abrir el circuito
            if "401" in str(e) or "Unauthorized" in str(e):
                raise e
            self._on_fallo(e)
            raise e

    def _on_exito(self):
        if self.estado == EstadoCircuito.SEMIABIERTO:
            print("🟢 [CB] Prueba exitosa. Transición a CERRADO.")
        self.estado = EstadoCircuito.CERRADO
        self.fallos = 0

    def _on_fallo(self, e):
        self.fallos += 1
        if self.estado == EstadoCircuito.CERRADO and self.fallos >= self.umbral:
            print(f"🔴 [CB] Umbral de fallos alcanzado ({self.fallos}). Transición a ABIERTO.")
            self.estado = EstadoCircuito.ABIERTO
            self._tiempo_apertura = time.time()
        elif self.estado == EstadoCircuito.SEMIABIERTO:
            print("🔴 [CB] Fallo en prueba piloto. Regresando a ABIERTO.")
            self.estado = EstadoCircuito.ABIERTO
            self._tiempo_apertura = time.time()