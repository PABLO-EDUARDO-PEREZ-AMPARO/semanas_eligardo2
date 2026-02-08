import logging
import time
import functools

# --- CONFIGURACIÓN DEL SISTEMA DE LOGS ---
logging.basicConfig(
    level=logging.INFO, # INFO muestra resumen. Cambia a DEBUG para ver headers.
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)
logger = logging.getLogger("EcoMarketMonitor")

# Claves sensibles para censurar en los logs
SENSITIVE_KEYS = {'authorization', 'token', 'apikey', 'password', 'secret'}

def _sanitizar(data):
    """Oculta datos sensibles."""
    if not isinstance(data, dict): return data
    clean = data.copy()
    for k, v in clean.items():
        if k.lower() in SENSITIVE_KEYS:
            clean[k] = f"{str(v)[:4]}...[REDACTED]"
    return clean

def auditar_peticion_http(func):
    """
    DECORADOR: Mide tiempo, status y tamaño de cada petición automáticamente.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 1. Preparación
        method = args[0] if len(args) > 0 else kwargs.get('method', '???')
        url = args[1] if len(args) > 1 else kwargs.get('url', '???')
        
        # Log de entrada (solo nivel DEBUG)
        headers = kwargs.get('headers', {})
        logger.debug(f"🛫 OUTGOING: {method} {url} | Headers: {_sanitizar(headers)}")

        start_time = time.perf_counter()
        response = None
        error_capturado = None

        try:
            # 2. Ejecución real
            response = func(*args, **kwargs)
            return response
        
        except Exception as e:
            error_capturado = e
            raise # Pasamos el error al cliente para que decida qué hacer
        
        finally:
            # 3. Reporte Post-Mortem
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Datos de respuesta
            status = response.status_code if response else 0
            size_bytes = len(response.content) if response and response.content else 0
            
            # Mensaje base
            log_msg = f"{method} {url} | Status: {status} | Time: {duration_ms:.2f}ms | Size: {size_bytes}B"

            # Semáforo de logs
            if error_capturado or status >= 500:
                logger.error(f"🔥 FAILED: {log_msg} | Err: {error_capturado if error_capturado else 'Server Error'}")
            elif 400 <= status < 500:
                logger.error(f"❌ CLIENT ERR: {log_msg}")
            elif duration_ms > 2000:
                logger.warning(f"🐢 SLOW REQ: {log_msg} (Lento)")
            else:
                logger.info(f"✅ SUCCESS: {log_msg}")

    return wrapper