# Autopsia de Bugs - Grand Deploy EcoMarket
**Componente:** ClienteRobusto / CircuitBreaker  
**Objetivo:** Auditoría de resiliencia, seguridad y arquitectura.

---

 Bug A: Error de permisos 'viewer'

* **Síntoma:** Los operadores con rol 'viewer' reciben un error de permisos al consultar inventario, aunque deberían poder hacer GET.
* **Causa raíz:** El `CircuitBreaker` está extrayendo y decodificando el token JWT para validar roles de usuario, mezclando la lógica de autorización del sistema con la lógica de resiliencia de red.
* **Línea exacta:** Dentro del método `ejecutar()` del `CircuitBreaker` (Bloque `if token_manager: ... raise PermissionError(...)`).
* **Corrección:** ```python
  # Eliminar por completo este bloque de código del CircuitBreaker
  # y no pasar token_manager como parámetro en la llamada lambda.
Principio violado: Separación de Responsabilidades (SRP - Single Responsibility Principle). El único trabajo del Circuit Breaker es vigilar la salud de la red y los tiempos de espera. No debe conocer la existencia de JWTs ni aplicar reglas de negocio.

Bug B: Fragmentos del token en logs
Síntoma: En los logs de producción aparecen fragmentos del token de acceso.

Causa raíz: Al capturar una excepción en el ClienteRobusto, la instrucción de logging está imprimiendo explícitamente los primeros 40 caracteres de la cabecera HTTP de Autorización.

Línea exacta: Dentro del bloque except de get_inventario() en ClienteRobusto.

Python
logger.error(f"Error: {e}. Auth: {headers['Authorization'][:40]}...")
Corrección:

Python
# Modificar el log para no acceder al diccionario de headers
logger.error(f"Error de conexión: {e}")
Principio violado: Seguridad y Prevención de Fugas de Datos (No Logging of Secrets). Es un Hard Gate de seguridad; credenciales, tokens o contraseñas jamás deben persistirse en los logs, ya que vulnera la privacidad y seguridad del clúster de producción.

Bug C: El contador no se reinicia
Síntoma: Después de que el servidor se recupera y el circuito cierra, sigue acumulando fallos como si fuera la primera vez — el contador no se reinicia.

Causa raíz: Cuando la petición de prueba en estado SEMIABIERTO es exitosa, el método _on_exito() cambia el estado a CERRADO, pero retiene en memoria la cantidad de fallos pasados.

Línea exacta: Dentro del método _on_exito(self): en la transición de estado.

Corrección: ```python
def _on_exito(self):
self.estado = EstadoCircuito.CERRADO
self._fallos = 0  # <--- LÍNEA AGREGADA

Principio violado: Integridad de la Máquina de Estados (State Machine Invariants). Al realizar una transición de estado de recuperación total (de SEMIABIERTO a CERRADO), es imperativo reiniciar las métricas y variables de control históricas para mantener la coherencia matemática del nuevo estado.