# Semana 6 - Cliente Server-Sent Events (SSE) EcoMarket

## Instrucciones de Ejecución
1. Asegúrate de tener Python 3.7+ instalado.
2. Instala la dependencia requerida ejecutando en tu terminal:
   `python -m pip install httpx`
3. Ejecuta el cliente con el comando:
   `python receptor_alertas.py`

## Traza del Reto 1: Flujo de una Sesión SSE
A continuación se explica el ciclo de vida de la conexión SSE diseñado para EcoMarket:

* **0s (Conexión):** El cliente envía un `GET` con el header `Accept: text/event-stream`. El servidor responde `200 OK` y deja la línea abierta.
* **Ts (Eventos):** El servidor envía eventos en texto plano (`id`, `event`, `data`) separados por `\n\n`. El cliente procesa eventos como `precio-actualizado` y `stock-critico`.
* **15s (Keep-Alive):** El servidor envía `: ping`. El cliente lo ignora, pero esto evita que el router cierre la conexión inactiva.
* **25s (Caída):** Falla la red. El cliente detecta la interrupción y espera el tiempo definido por el protocolo (retry).
* **28s (Reconexión):** El cliente intenta conectarse de nuevo incluyendo el header mágico `Last-Event-ID: {ultimo_id}` para que el servidor le envíe únicamente los eventos que se perdió durante la caída.


Decisión de Arquitectura: Composición vs. Herencia en el Patrón Observable
Para integrar el sistema de eventos, elegí utilizar Composición (self.tablero_eventos = Observable()) en lugar de hacer que ReceptorAlertas herede de la clase Observable. Esto respeta el principio de Responsabilidad Única y la regla de "favorecer la composición sobre la herencia". Un cliente de red no es un notificador de eventos, sino que utiliza un notificador de eventos. Mediante la composición, encapsulamos la lógica del Observable, protegiendo sus métodos internos y evitando que cualquier otra parte del sistema dispare eventos falsos a través del receptor de red.