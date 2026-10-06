# MEMORY.md - Bitácora de Estado
## Estado Actual
- Fase: Spec 001 - Tarea T5 completada.
- Modelos acordados: Cloudflare/clef-flash (local, 4-bit NF4) y Google Gemini 2.5 Flash (Cloud, AI Studio).
- T1 (Schemas y Contratos): Implementados en `backend/app/schemas.py` con 24 tests unitarios pasando en verde en `backend/tests/test_schemas.py`.
- T2 (Servicio Clef-Flash Local): Implementado en `backend/app/services/clef_service.py` con 3 tests pasando en verde en `backend/tests/test_clef_service.py`.
- T3 (Servicio Cloud Gemini 2.5 Flash): Implementado en `backend/app/services/gemini_service.py` con SDK oficial `google-genai` (v2.28.0) y 11 tests pasando en verde (10 mocks + 1 test de integración real `test_gemini_live_integration` validado exitosamente contra Google AI Studio usando `gemini-2.5-flash`). Se registró `GEMINI_MODEL="gemini-2.5-flash"` en `backend/.env` debido a la deprecación de `gemini-2.0-flash` por parte de Google.
- T4 (Endpoint Comparativo en FastAPI y Mapeador Jira): Implementados `backend/app/services/jira_mapper.py` y `backend/app/main.py` con 11 tests pasando en verde en `tests/test_jira_mapper.py` y `tests/test_api.py`. Soporta ejecución paralela no bloqueante vía `asyncio.to_thread` / `asyncio.gather`, detección de discrepancias actuariales y generación de tickets duales para siniestros P1 o MIXTO.
- T5 (Setup del Frontend React + Tailwind CSS): Inicializado en `/frontend` con Vite, React 19, TypeScript, Tailwind CSS y Lucide-React. Tipado estricto en `frontend/src/types/triage.ts`, proxy a `http://localhost:8000` y componentes base estructurados (`Header`, `ClaimInput`, `ComparisonCards`, `JiraPreview`, `CostAnalysis`). Compilación exitosa en verde (`npm run build`).

## Métricas de Hardware y Telemetría Clef-Flash (RTX 4060 8GB VRAM)
- Modelo: `Cloudflare/clef-flash` (Backbone Qwen3.5-9B cuantizado 4-bit NF4 + JointSchemaHead en bfloat16).
- VRAM asignada tras carga (`torch.cuda.memory_allocated()`): **3.569 GB** (3,654.6 MiB), holgadamente por debajo del límite constitucional de 6.2 GB.
- VRAM pico durante inferencia (`torch.cuda.max_memory_allocated()`): **5.471 GB** (5,602.3 MiB).
- Tiempo de carga de modelo + warm-up: **37.96 s**.
- Latencia de inferencia (forward pass completo de triage con 1,000 tokens de prompt y 6 campos del esquema evaluados simultáneamente): **mediana de 1,164.3 ms** (máximo 1,185.4 ms) en la GPU de laptop RTX 4060.
- El Joint Schema Head por sí solo consume únicamente ~10 ms; la mayor parte del tiempo se invierte en el backbone Qwen3.5-9B NF4 sobre CUDA.

## Decisiones Técnicas
- Se descarta Streamlit por falta de control sobre micro-latencias y diseño visual corporativo.
- Frontend se desarrollará con React + Tailwind para permitir visualizaciones paralelas con streaming real.
- Backend configurado con virtualenv Python 3.11.15 (`backend/.venv`) vía `uv` para garantizar compatibilidad estricta con Pydantic v2 y futuros frameworks de inferencia (PyTorch/Transformers) en CachyOS.
- Modelos Pydantic incluyen validación cruzada actuarial estricta: consistencia entre Macro-Ramo y Ramo Específico, validación de catálogos cerrados y rangos de severidad con mapeo SLA Jira.
- En `gemini_service.py`, se utiliza el SDK unificado oficial `google-genai` (v2.28.0) con el modelo `gemini-2.5-flash` (configurable vía `GEMINI_MODEL`). Se configuran Structured Outputs forzando `response_mime_type="application/json"` y `response_schema=TriageDecision` con `temperature=0.0` para garantizar determinismo y cumplimiento estricto del contrato actuarial sin regex frágiles.
- La telemetría de Gemini extrae `prompt_token_count` y `candidates_token_count` de `usage_metadata`, midiendo la latencia de red+inferencia con `time.perf_counter()`. Se calcula el costo por llamada y proyectado a 100k transacciones con las tarifas oficiales ($0.075 / 1M input tokens, $0.30 / 1M output tokens).
- Autenticación requiere `GEMINI_API_KEY` o paso explícito al instanciar `GeminiService`, lanzando `RuntimeError("GEMINI_API_KEY no configurada")` si no está presente.
- La suite de pruebas en `test_gemini_service.py` aísla los tests continuos con `unittest.mock` para cero consumo de cuota ni dependencia de internet, e incluye un test condicional `@pytest.mark.skipif` para integración real cuando se defina la clave.
- En `jira_mapper.py`, se implementa la lógica de doble ticket (`is_dual_ticket=True`): cualquier siniestro con severidad 1 (P1) o con `macro_ramo == MIXTO` genera automáticamente dos tickets enlazados en Jira: Ticket Patrimonial (componente en Ramos Generales) y Ticket de Personas (componente en Vida/Personas con SLA prioritario de hasta 2 horas).
- En `main.py`, el endpoint `/api/triage/compare` delega la inferencia de Clef y Gemini a hilos de trabajo mediante `asyncio.to_thread` y los coordina concurrentemente con `asyncio.gather`. Esto previene el bloqueo del event loop de FastAPI durante el forward pass de PyTorch sobre CUDA.
- Se configuró middleware CORS en FastAPI para permitir integración directa y fluida con el frontend React + Vite en desarrollo.
- En el frontend (`/frontend`), se configuró Vite con `@tailwindcss/vite` y proxy inverso hacia `http://localhost:8000` en `vite.config.ts` para todas las rutas `/api/*`.
- Contratos TypeScript en `src/types/triage.ts` garantizan paridad tipada 1:1 con `schemas.py` de FastAPI.
- La suite de componentes base (`Header`, `ClaimInput`, `ComparisonCards`, `JiraPreview`, `CostAnalysis`) utiliza paleta oscura corporativa (zinc/emerald/sky) estilo Linear/Vercel con soporte visual para doble ticket, banderas de discrepancia y simulador dinámico de costos.

## Errores a Evitar
- No cargar modelos en FP16 en la RTX 4060 (provoca Out Of Memory).
- Evitar usar el Python 3.14 global del sistema por inconsistencia de `pydantic-core` en paquetes rolling de CachyOS; usar siempre el entorno virtual en `backend/.venv`.
- No intentar instanciar `AutoProcessor` para tareas de solo texto de Clef-Flash si torchvision no está compilado, ya que el video processor exige `torchvision`; usar `AutoTokenizer` directamente.