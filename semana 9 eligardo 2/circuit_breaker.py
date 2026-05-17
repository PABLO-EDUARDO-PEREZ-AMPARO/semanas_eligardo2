"""
DECISIONES DE DISEÑO (Reto 1):
 1. ¿Qué errores cuentan como fallo del servidor?
    R = Errores 5xx, timeouts de red (asyncio.TimeoutError), conexiones rechazadas
        (ConnectionRefusedError), errores de socket (OSError) y el error 429 (Too Many Requests).
 2. ¿Qué umbral de fallos elegiste y por qué?
    R = 5 fallos consecutivos. Es una media estándar en la industria que balancea de manera 
        óptima la sensibilidad del sistema sin sobrecargar al servidor afectado.
 3. ¿Qué timeout de apertura elegiste y por qué?
    R = 60.0 segundos (o 30s según necesidad). 60 segundos proporciona un margen saludable 
        para que los servicios del backend de EcoMarket se restablezcan, limpien colas o reinicien.

TABLA DE CLASIFICACIÓN (Reto 2):
 | Escenario | Clasificación | Justificación (Perspectiva del Cliente) |

 | 1. 503 Service Unavailable | FALLO | Servidor saturado o en mantenimiento programado. |
 | 2. 401 Unauthorized | IGNORAR | El backend responde correctamente; las credenciales del cliente expiraron. |
 | 3. Timeout (30s) | FALLO | Saturación de red o colapso en el backend que impide toda respuesta. |
 | 4. 404 Not Found | IGNORAR | Lógica de negocio; la ruta o producto no existe, pero el servidor está sano. |
 | 5. Connection Refused | FALLO | Fallo de infraestructura crítico: el servidor está apagado o no escucha el puerto. |
 | 6. 500 Internal Server Error| FALLO | Error no controlado dentro del código del backend (inestabilidad). |
 | 7. 429 Too Many Requests | FALLO | Caso especial: Rate limiting severo. El servidor ruega detener el tráfico. |
 | 8. 403 Forbidden | IGNORAR | El servidor opera a la perfección, simplemente rechaza al cliente por falta de permisos. |
"""

import asyncio
import time
from enum import Enum, auto


class EstadoCircuito(Enum):
    CERRADO     = auto()   
    ABIERTO     = auto()  
    SEMIABIERTO = auto() 


class CircuitOpenError(Exception):
    """El circuito está abierto — no se intentó la petición."""
    def __init__(self, tiempo_restante: float):
        self.tiempo_restante = tiempo_restante
        super().__init__(
            f"Circuit breaker abierto. Reintenta en {tiempo_restante:.1f}s"
        )


class CircuitBreaker:
    """
    Implementa el patrón Circuit Breaker del lado del cliente.
    
    El cliente llama a cb.ejecutar(coro) en lugar de await coro directamente.
    Si el circuito está abierto, lanza CircuitOpenError inmediatamente.
    """

    def __init__(
        self,
        umbral_fallos: int = 5,
        timeout_apertura: float = 60.0,
        nombre: str = "EcoMarketAPI"
    ):
        self.nombre = nombre
        self.umbral_fallos = umbral_fallos
        self.timeout_apertura = timeout_apertura
        
        self._estado = EstadoCircuito.CERRADO
        self._fallos_consecutivos = 0
        self._tiempo_apertura = None
        
        # SOLUCIÓN INV-A2: Bandera booleana simple, NO un Lock
        self._sonda_en_vuelo = False 
        
        print(f"🛡️ [{self.nombre}] Circuit Breaker inicializado en estado CERRADO.")

    @property
    def estado(self) -> EstadoCircuito:
        """Retorna el estado actual. Lee _revisar_timeout() antes de retornar."""
        self._revisar_timeout()
        return self._estado

    @property
    def esta_abierto(self) -> bool:
        return self.estado == EstadoCircuito.ABIERTO

    def _revisar_timeout(self) -> None:
        """
        Si el circuito está ABIERTO y el timeout_apertura expiró,
        transiciona a SEMIABIERTO para permitir una petición de prueba.
        """
        if self._estado == EstadoCircuito.ABIERTO:
            if self._tiempo_apertura is not None:
                tiempo_transcurrido = time.monotonic() - self._tiempo_apertura
                
                if tiempo_transcurrido >= self.timeout_apertura:
                    self._estado = EstadoCircuito.SEMIABIERTO
                    print(f"⏳ [{self.nombre}] El tiempo de espera ({self.timeout_apertura}s) terminó.")
                    print(f"🔄 [{self.nombre}] Transición de estado: ABIERTO ➔ SEMIABIERTO. Listo para enviar 1 petición de prueba.")

    def _es_fallo_servidor(self, excepcion: Exception) -> bool:
        """
        Decide si una excepción debe contar como fallo del servidor.
        """
        if isinstance(excepcion, (asyncio.TimeoutError, ConnectionRefusedError, OSError)):
            return True
            
        status_code = getattr(excepcion, 'status', getattr(excepcion, 'status_code', None))
        
        if status_code is not None:
            if status_code >= 500:
                return True
            if status_code == 429:
                return True
            if 400 <= status_code < 500:
                return False

        return False

    def _registrar_exito(self) -> None:
        """Registra éxito: resetea contador y cierra el circuito."""
        self._fallos_consecutivos = 0
        
        if self._estado == EstadoCircuito.SEMIABIERTO:
            self._estado = EstadoCircuito.CERRADO
            print(f"✅ [{self.nombre}] Petición de prueba exitosa.")
            print(f"🔄 [{self.nombre}] Transición de estado: SEMIABIERTO ➔ CERRADO. Circuito restablecido.")

    def _registrar_fallo(self) -> None:
        """Registra fallo del servidor: incrementa contador o abre el circuito."""
        self._fallos_consecutivos += 1
        
        if self._estado == EstadoCircuito.CERRADO:
            print(f"⚠️ [{self.nombre}] Fallo detectado ({self._fallos_consecutivos}/{self.umbral_fallos}).")
            
            if self._fallos_consecutivos >= self.umbral_fallos:
                self._estado = EstadoCircuito.ABIERTO
                self._tiempo_apertura = time.monotonic()
                print(f"🚨 [{self.nombre}] Umbral de fallos alcanzado.")
                print(f"🔄 [{self.nombre}] Transición de estado: CERRADO ➔ ABIERTO. Tráfico bloqueado por {self.timeout_apertura}s.")
                
        elif self._estado == EstadoCircuito.SEMIABIERTO:
            self._estado = EstadoCircuito.ABIERTO
            self._tiempo_apertura = time.monotonic()
            print(f"❌ [{self.nombre}] Petición de prueba fallida. El servidor sigue inestable.")
            print(f"🔄 [{self.nombre}] Transición de estado: SEMIABIERTO ➔ ABIERTO. Tráfico bloqueado nuevamente.")

    async def ejecutar(self, coro):
        """
        Punto de entrada principal.
        Flujo de control resiliente implementado rigurosamente.
        """
        estado_actual = self.estado
        if estado_actual == EstadoCircuito.ABIERTO:
            tiempo_transcurrido = time.monotonic() - self._tiempo_apertura
            tiempo_restante = max(0.0, self.timeout_apertura - tiempo_transcurrido)
            raise CircuitOpenError(tiempo_restante)
        peticion_de_prueba = False
        if estado_actual == EstadoCircuito.SEMIABIERTO:
            if self._sonda_en_vuelo:
                raise CircuitOpenError(self.timeout_apertura)
            
            self._sonda_en_vuelo = True
            peticion_de_prueba = True
        try:
            resultado = await coro
            self._registrar_exito()
            return resultado

        except Exception as e:
            if self._es_fallo_servidor(e):
                self._registrar_fallo()
            raise

        finally:
            if peticion_de_prueba:
                self._sonda_en_vuelo = False

                