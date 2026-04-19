# Panel de Control EcoMarket - Cliente SSE Multiplex

## Decisiones de diseño — entendidas antes de codificar

En esta sección se documentan las bases teóricas y las limitaciones técnicas comprendidas antes de la implementación del cliente multiplexado para EcoMarket.

### 1. Límites de conexión en el navegador (The "6-Connection" Rule)
* **Análisis:** Si abro 3 objetos `EventSource` hacia el mismo origen y el límite es 6, quedan **3 conexiones libres**. Si el cupo de 6 conexiones se llena con flujos SSE persistentes, cualquier intento de hacer un `fetch()` quedará bloqueado o en cola (esperando en la "calle"), lo que puede congelar la experiencia del usuario o causar errores de tiempo de espera (timeout).

### 2. Límites en entornos de servidor (Python/Node.js)
* **Análisis:** En lenguajes de backend como Python no existe el límite artificial de 6 conexiones que imponen los navegadores. La limitación es puramente **física y de hardware**: memoria RAM disponible, capacidad de procesamiento de la CPU y la cantidad de puertos de red que el SO puede gestionar antes de colapsar.

### 3. Gestión de eventos no controlados (Event Handlers)
* **Análisis:** Si el cliente recibe un evento para el cual no tiene un suscriptor registrado (ej. módulo inactivo), el programa debe **ignorarlo en silencio**. No debe lanzar una excepción ni detenerse. Es un patrón de "disparar y olvidar" para no afectar la estabilidad del resto de la aplicación.

### 4. Dinamismo de la conexión y Handshake
* **Análisis:** No se pueden añadir módulos a la URL de una conexión SSE activa sin reconectar. Debido a la naturaleza del "apretón de manos" de HTTP, los parámetros se definen al inicio. Una vez abierta la conexión, cualquier cambio en la suscripción requiere cerrar el socket y abrir uno nuevo.

---
### Síntesis de Arquitectura
1. **Multiplexación obligatoria:** Dado el límite de los navegadores, se usa una sola conexión SSE (`ClienteSSEMultiplex`) para múltiples módulos.
2. **Estatismo de la conexión:** El cliente aplica el Invariante C3 (INV-C3) asegurando que la URL se construye correctamente antes del inicio.
3. **Resiliencia:** Se implementó un bloque `try/except` en el `EventRouter` para evitar que una falla en un handler corrompa el ciclo de vida de la conexión SSE completa.