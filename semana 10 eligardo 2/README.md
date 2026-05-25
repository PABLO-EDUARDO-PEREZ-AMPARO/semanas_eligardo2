# 🛡️ E-Commerce Resiliente: Hito 2

Sistema de cliente HTTP tolerante a fallos, implementando los patrones **Circuit Breaker** y **Token Manager** con soporte para concurrencia segura y manejo de flujos SSE.

## 🛠️ Entorno y Requisitos
* **Lenguaje:** Python 3.12+
* **Dependencias:** `pytest`, `pytest-asyncio`

## ⚙️ Estructura del Código (Arquitectura SRP)
Para evadir colisiones y mantener el código limpio, el sistema se divide en:
1. `circuit_breaker.py`: Lógica pura de resiliencia y estados (CERRADO, ABIERTO, SEMIABIERTO).
2. `token_manager.py`: Lógica de seguridad JWT e interceptación de errores de decodificación.
3. `cliente_robusto.py`: Orquestador principal.

## 🚀 Cómo ejecutar las pruebas automatizadas
Para validar los invariantes de seguridad y concurrencia (Thundering Herd y TC-X2), ejecuta en la terminal:

```bash
pytest test_circuit_breaker.py
pytest test_tc_x2_refresh_semiabierto.py