# Reporte de Seguridad: Autenticación en Clientes SSE
**Autor:** Pablo Eduardo Perez Amparo
**Proyecto:** TechNova / EcoMarket

## 1. Pregunta Central: ¿Soporta la API nativa `EventSource` el envío de headers custom (como `Authorization: Bearer`)?

**La respuesta directa es NO.** La API nativa `EventSource` del navegador no permite inyectar headers personalizados. Esto no es un error, sino una decisión de diseño de la W3C por dos motivos principales:
1. **Simplicidad:** Fue diseñada para ser tan fácil de usar como una etiqueta `<img>` o `<script>`, delegando toda la gestión de red al navegador.
2. **Reconexión Automática:** El "superpoder" de `EventSource` es que se reconecta solo si la red falla. Si permitiera headers dinámicos (como un token que expira), el navegador no sabría cómo pedir un token nuevo para inyectarlo en el reintento automático en segundo plano, lo que rompería la reconexión. Por ello, asume que la autenticación web debe manejarse mediante Cookies.

---

## 2. Contexto B: Alternativas en el Navegador (Frontend)

Dado que no podemos usar headers nativos, aquí están las 4 opciones reales para autenticar nuestro panel de EcoMarket, con sus pros y contras:

| Alternativa | Pros (Ventajas) | Contras (Desventajas) | Recomendación |
| :--- | :--- | :--- | :--- |
| **1. Cookies (`withCredentials: true`)** | Es la forma nativa y más segura si se usan cookies `HttpOnly` (inmunes a XSS). El navegador hace todo solo. | Obliga al backend a manejar sesiones por cookies, rompiendo el diseño estricto de una API 100% Stateless (sin estado). | **Ideal** si el backend colabora y puede emitir cookies seguras. |
| **2. Token en URL (`?token=XYZ`)** | Es facilísimo de implementar tanto en frontend como en backend. Funciona con `EventSource` nativo. | **Pésima seguridad.** El token queda expuesto para siempre en el historial del navegador, proxies corporativos y logs del servidor (ej. Nginx). | **Evitar a toda costa** en entornos de producción. |
| **3. Librería `@microsoft/fetch-event-source`** | Permite inyectar headers (como Bearer) fácilmente. No expone el token en la URL. Es un estándar en la industria (React/Angular). | Requiere instalar una dependencia extra y abandona la API nativa `EventSource` a favor de un `fetch` procesado manualmente. | **La mejor opción** si el backend exige estrictamente JWT Bearer Tokens. |
| **4. Interceptor con Service Worker** | Permite mantener el código UI limpio usando `EventSource` nativo, inyectando el header justo antes de salir a la red. | Es matar una mosca con una bazuca. La gestión del ciclo de vida de los Service Workers es un infierno de depurar para apps sencillas. | **No recomendado** a menos que sea una PWA compleja con modo offline avanzado. |

---

## 3. Contexto A: Flujo de Renovación en Cliente Python/Node.js

En un cliente de servidor a servidor (como nuestro script de Python), sí tenemos control total de los headers. Este es el pseudocódigo para manejar la expiración del token sin perder eventos:

```python
FUNCION conectar_sse_seguro():
    token_actual = obtener_token_valido()
    ultimo_id = NULO
    
    MIENTRAS el_sistema_este_corriendo:
        headers = {
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {token_actual}",
            "Last-Event-ID": ultimo_id
        }
        
        INTENTAR:
            conexion = ABRIR_STREAM("GET", url, headers)
            
            SI conexion.codigo_estado == 401 (No Autorizado):
                # El token expiró. Pausamos el stream y renovamos.
                token_actual = REFRESCAR_TOKEN_EN_API()
                CONTINUAR_BUCLE # Vuelve a intentar conectar con el nuevo token
            
            # Si el código es 200 OK, procesamos los datos
            MIENTRAS lleguen_lineas_en(conexion):
                evento = parsear_linea()
                ultimo_id = evento.id
                procesar_evento(evento)
                
        CAPTURAR ERROR_DE_RED:
            ESPERAR(3_segundos) # Intento de reconexión