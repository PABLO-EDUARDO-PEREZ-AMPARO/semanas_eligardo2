# ☑️ Checklist de Invariantes y Certificación

| Invariante | Descripción | Estado | Evidencia |
| :--- | :--- | :--- | :--- |
| **INV-A1** | SRP Estricto en Circuit Breaker | ✅ PASS | `circuit_breaker.py` no tiene atributos ni menciones a JWT, exp, ni tokens. Inmune a errores de decodificación. |
| **INV-A2** | Thundering Herd en SEMIABIERTO | ✅ PASS | Validación de código en `test_circuit_breaker.py` (Lanza error rápido si un segundo request intenta pasar cuando el piloto ya voló). |
| **INV-A3** | Transiciones de Estado | ✅ PASS | Logs demostrados en consola (`demo_resiliencia.log`): CERRADO → ABIERTO → SEMIABIERTO → CERRADO. |
| **INV-A4** | 401 Unauthorized no abre CB | ✅ PASS | Filtro inteligente en bloque `except` de `circuit_breaker.py` lanza el 401 directamente sin incrementar contador de fallos. |
| **INV-B1** | SRP Estricto en Token Manager | ✅ PASS | `token_manager.py` no contiene variables `_estado` ni menciones a lógicas de circuito abierto/cerrado. |
| **INV-B2** | Refresh Singleton | ✅ PASS | Aislamiento lógico. Renovar el token es un proceso independiente y anterior a las llamadas de red protegidas. |
| **INV-B3** | Decodificación Base64 Segura | ✅ PASS | Bloque `try-except` en `is_expiring_soon()` que intercepta tokens mal formados y devuelve `True` sin romper la ejecución. |

**Conclusión:** El sistema supera el "Hard Gate" de seguridad y mantiene separación estricta de responsabilidades (SRP).