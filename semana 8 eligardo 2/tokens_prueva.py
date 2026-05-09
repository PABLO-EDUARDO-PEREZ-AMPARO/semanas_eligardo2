"""── Caso 1: Token bien formado, no expirado ─────────────────────────────
  Header:  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
  Payload: eyJzdWIiOiJ1c2VyXzEiLCJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcxNDAwMH0
  Sig:     cualquiercosa
  Token:   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEiLCJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcxNDAwMH0.cualquiercosa
  Payload decodificado: {"sub":"user_1","exp":9999999999,"iat":1714000}
  → Resultado esperado: is_expiring_soon() = False

── Caso 2: Token expirado hace 10 minutos ──────────────────────────────
  Payload (base64url): eyJzdWIiOiJ1c2VyXzIiLCJleHAiOjE3MDAwMDAwMDAsImlhdCI6MTcwMDAwMDAwMH0
  Payload decodificado: {"sub":"user_2","exp":1700000000,"iat":1700000000}
  → Resultado esperado: is_expiring_soon() = True (ya expiró)

── Caso 3: Token malformado — solo 2 partes ───────────────────────────
  Token:   eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyXzMifQ
  → Resultado esperado: decode_payload() lanza ValueError controlado, NO IndexError sin capturar

── Caso 4: Token con payload inválido (no es JSON válido) ─────────────
  Token:   eyJhbGciOiJIUzI1NiJ9.bm9fanNvbg.firma
  Payload base64url = "no_json" (texto plano que no es JSON)
  → Resultado esperado: decode_payload() lanza ValueError o JSONDecodeError controlado

── Caso 5: Token sin campo exp ────────────────────────────────────────
  Payload decodificado: {"sub":"user_5","iat":1714000000}
  → Resultado esperado: is_expiring_soon() retorna True (tratar como expirado si no hay exp)
  ¿Tu implementación maneja el KeyError/undefined de acceder a exp inexistente?

── Caso 6: Refresh simultáneo — prueba del singleton ──────────────────
  Simula 5 co-rutinas/promesas concurrentes que llaman a refresh() al mismo tiempo.
  → Resultado esperado: SOLO UNA petición real al servidor de refresh.
  → Las otras 4 reciben el resultado de la primera.
  ¿Cómo verificas esto? Añade un contador de llamadas reales al endpoint de refresh."""