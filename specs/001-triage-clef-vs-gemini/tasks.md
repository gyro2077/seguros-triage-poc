# Tasks: Spec 001 - Triage Engine

- [x] **T1. Schemas y Contratos de Dominio Actuarial.**
  - Crear `backend/app/schemas.py` con los modelos Pydantic de entrada, salida y Jira issues según la regulación de seguros.
  - Hecho cuando: `pytest tests/test_schemas.py` valide la serialización de todos los ramos y rechace enums inválidos.

- [x] **T2. Servicio de Inferencia Local Clef-Flash.**
  - Implementar `backend/app/services/clef_service.py` cargando `Cloudflare/clef-flash` en 4-bit para la GPU de 8GB.
  - Hecho cuando: Una prueba unitaria confirme inferencia en un solo forward pass en menos de 150 ms sin desbordar la VRAM de la RTX 4060.

- [x] **T3. Servicio Cloud Gemini 2.5 Flash.**
  - Implementar `backend/app/services/gemini_service.py` con Google GenAI SDK forzando JSON schema tipado.
  - Hecho cuando: El servicio devuelva la estructura de clasificación junto con métricas de tokens consumidos y latencia de red.

- [x] **T4. Endpoint Comparativo en FastAPI y Mapeador Jira.**
  - Crear endpoint `POST /api/triage/compare` que ejecute ambos servicios en paralelo (`asyncio.gather`) y genere el payload de Jira.
  - Hecho cuando: Una llamada cURL a `/api/triage/compare` devuelva ambas respuestas simultáneas con código 200.

- [ ] **T5. Setup del Frontend React + Tailwind.**
  - Inicializar cliente en `/frontend` con Vite, Tailwind CSS y componentes base de diseño oscuro corporativo.
  - Hecho cuando: `npm run build` termine sin errores de TypeScript y la pantalla base renderice en el navegador.

- [ ] **T6. Integración y Validación de la Demo Visual.**
  - Conectar el formulario de incidentes al backend y construir los paneles de resultados, latencia comparativa y simulador de costos.
  - Hecho cuando: Al enviar un siniestro de prueba, la interfaz pinte las tarjetas de Clef (verde, ultra-rápida) y Gemini, renderizando los tickets enlazados de Jira correspondientes.