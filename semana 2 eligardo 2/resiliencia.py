# Archivo: resiliencia.py
import time
import random
import logging
from functools import wraps
import requests

# Configuración de logs para ver qué pasa en consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ResilienceEngine")

def with_retry(max_retries=3, base_delay=1, backoff_factor=2):
    """
    Decorador para reintentar operaciones HTTP con Exponential Backoff + Jitter.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt <= max_retries:
                try:
                    return func(*args, **kwargs)
                
                except requests.RequestException as e:
                    # 1. Obtener status code si existe
                    status_code = e.response.status_code if e.response is not None else None
                    
                    # 2. NO REINTENTAR errores 4xx (excepto quizás 429, pero por ahora lo dejamos simple)
                    if status_code and 400 <= status_code < 500:
                        logger.error(f"❌ Error de cliente ({status_code}). No se reintenta.")
                        raise e

                    # 3. SI SE ACABARON LOS INTENTOS
                    if attempt == max_retries:
                        logger.critical(f"💀 Se agotaron los {max_retries} reintentos. Fallo final: {e}")
                        raise e

                    # 4. CALCULAR TIEMPO DE ESPERA (Backoff + Jitter)
                    delay = base_delay * (backoff_factor ** attempt)
                    jitter = random.uniform(0, 1)
                    total_sleep = delay + jitter

                    logger.warning(
                        f"⚠️ Intento {attempt + 1}/{max_retries} falló ({e}). "
                        f"Reintentando en {total_sleep:.2f}s..."
                    )
                    
                    time.sleep(total_sleep)
                    attempt += 1
        return wrapper
    return decorator