import asyncio
import aiohttp
import time
from dataclasses import dataclass

@dataclass
class PoolMetrics:
    created: int = 0
    reused: int = 0
    closed: int = 0

class SmartSession(aiohttp.ClientSession):
    def __init__(self, limit=20, limit_per_host=0, *args, **kwargs):
        # Configuración del conector (el cerebro del pool)
        self.connector = aiohttp.TCPConnector(
            limit=limit, 
            limit_per_host=limit_per_host,
            keepalive_timeout=60 # Segundos que la conexión vive sin uso
        )
        super().__init__(connector=self.connector, *args, **kwargs)
        self.metrics = PoolMetrics()

    def get_pool_status(self):
        """Monitorea el estado actual del pool"""
        return {
            "total_limit": self.connector.limit,
            "active_connections": len(self.connector._conns),
            "acquired": self.connector._acquired_per_host, # Conexiones en uso
            "available": self.connector.limit - len(self.connector._acquired),
            "waiting": len(self.connector._waiters) # Peticiones en cola
        }

    async def health_check(self):
        """Verifica si el pool está saturado"""
        status = self.get_pool_status()
        if status["waiting"] > 0:
            print(f"⚠️ Alerta: {status['waiting']} peticiones esperando en el pool.")
        else:
            print(f"✅ Pool saludable: {status['active_connections']} conexiones activas.")