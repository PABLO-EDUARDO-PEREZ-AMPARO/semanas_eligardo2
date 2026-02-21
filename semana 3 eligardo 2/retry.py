import time
import random
import logging
from functools import wraps
import requests

# Configuración básica de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RetryEngine")

def with_retry(max_retries=3, base_delay=1, backoff_factor=2):
    """
    Decorador para reintentar operaciones HTTP con Exponential Backoff + Jitter.
    
    Args:
        max_retries (int): Número máximo de intentos adicionales.
        base_delay (int): Tiempo base de espera en segundos.
        backoff_factor (int): Multiplicador para el tiempo de espera (exponencial).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt <= max_retries:
                try:
                    return func(*args, **kwargs)
                
                except requests.RequestException as e:
                    # 1. Análisis del error
                    status_code = e.response.status_code if e.response is not None else None
                    
                    # NO REINTENTAR errores de cliente (4xx), excepto quizás 429 (Too Many Requests)
                    if status_code and 400 <= status_code < 500:
                        logger.error(f"❌ Error de cliente ({status_code}). No se reintenta.")
                        raise e

                    # 2. Si se acabaron los intentos, lanzamos el error final
                    if attempt == max_retries:
                        logger.critical(f"💀 Se agotaron los {max_retries} reintentos. Fallo final: {e}")
                        raise e

                    # 3. Cálculo de espera (Backoff + Jitter)
                    delay = base_delay * (backoff_factor ** attempt)
                    jitter = random.uniform(0, 1) # Aleatoriedad para evitar colisiones
                    total_sleep = delay + jitter

                    logger.warning(
                        f"⚠️ Intento {attempt + 1}/{max_retries} falló por {e}. "
                        f"Reintentando en {total_sleep:.2f}s..."
                    )
                    
                    time.sleep(total_sleep)
                    attempt += 1
        return wrapper
    return decorator