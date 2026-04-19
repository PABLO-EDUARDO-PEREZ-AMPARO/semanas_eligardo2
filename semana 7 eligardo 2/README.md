## Decisiones de diseño — entendidas antes de codificar

En esta sección se documentan las bases teóricas y las limitaciones técnicas comprendidas antes de la implementación del cliente multiplexado para EcoMarket.

### 1. Límites de conexión en el navegador (The "6-Connection" Rule)
* **Pregunta:** Si abro 3 objetos `EventSource` hacia el mismo origen y el límite es 6, ¿cuántas quedan libres para `fetch()`? ¿Qué pasa si intento autenticarme con el cupo lleno?
* **Respuesta:** Quedan **3 conexiones libres**. Si el cupo de 6 conexiones se llena con flujos SSE persistentes, cualquier intento de hacer un `fetch()` quedará bloqueado o en cola (esperando en la "calle"), lo que puede congelar la experiencia del usuario o causar errores de tiempo de espera (timeout).

### 2. Límites en entornos de servidor (Python/Node.js)
* **Pregunta:** ¿Existe el mismo límite de 6 conexiones en Python? ¿Qué limita las conexiones en este caso?
* **Respuesta:** **No**, en Python no existe el límite artificial que imponen los navegadores. La limitación es puramente **física y de hardware**: memoria RAM disponible, capacidad de procesamiento de la CPU y la cantidad de puertos de red que el Sistema Operativo puede gestionar antes de colapsar.

### 3. Gestión de eventos no controlados (Event Handlers)
* **Pregunta:** ¿Qué debe hacer el cliente si recibe un evento (ej. `precio-actualizado`) para el cual no tiene un suscriptor registrado?
* **Respuesta:** El programa debe **ignorarlo en silencio**. No debe lanzar una excepción ni detenerse, ya que el sistema debe ser resiliente. Es un patrón de "disparar y olvidar": si nadie está interesado en el anuncio, este se descarta para no afectar la estabilidad del resto de la aplicación.

### 4. Dinamismo de la conexión y Handshake
* **Pregunta:** ¿Se pueden añadir módulos a la URL de una conexión SSE activa (ej. pasar de `?modulos=stock` a `?modulos=stock,devoluciones`) sin reconectar?
* **Respuesta:** **No es posible.** Debido a la naturaleza del "apretón de manos" (handshake) de HTTP, los parámetros de la URL se definen al inicio. Una vez que la "tubería" está abierta y fluyendo, no se puede cambiar su configuración. Es necesario cerrar la conexión actual y abrir una nueva con los nuevos parámetros.

---

### Síntesis Correctiva e Integral
Tras el análisis socrático, se concluye lo siguiente:
1. **Multiplexación obligatoria:** Dado el límite de 6 conexiones del navegador, la mejor práctica es usar una sola conexión SSE para múltiples módulos (multiplexar) en lugar de abrir una conexión por cada necesidad.
2. **Resiliencia:** El patrón Observer debe ser robusto; la ausencia de un suscriptor no es un error crítico del sistema, sino un estado normal de "ningún interesado".
3. **Estatismo de la conexión:** Entendemos que SSE es una conexión persistente basada en un estado inicial fijo. Cualquier cambio en la lógica de suscripción desde el cliente requiere un reinicio del ciclo de vida de la conexión HTTP.