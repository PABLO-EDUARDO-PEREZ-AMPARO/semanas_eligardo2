# Auditoría de Cliente SSE - Proyecto EcoMarket
**Autor:** Pablo Eduardo Perez Amparo

A continuación se documentan 4 errores sutiles encontrados en el código base del cliente SSE, los cuales pasaban las pruebas superficiales pero fallarían bajo condiciones de red reales en producción.

---

### 1. Error: La Brecha del Timeout (Conexiones Zombi)
* **Descripción:** Se configuró el cliente HTTP con `read=None`, asumiendo que el streaming no debía tener límite de lectura.
* **¿Cómo falla en producción?:** Si el módem pierde conexión física, el programa se queda esperando datos infinitamente, consumiendo RAM y nunca activa la reconexión.
* **Invariante violado:** Respetar los tiempos de espera de la red (timeout).
* **Evidencia de manifestación:**
  ```text
  ✅ Conectado a la API.
  📩 Evento procesado: precio | Datos: 45
  (Se desconecta el WiFi físicamente. El programa se congela en silencio).
  (Han pasado 10 minutos y no hay logs de reconexión ni errores).


  