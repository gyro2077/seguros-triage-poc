# MEMORY.md - Bitácora de Estado
## Estado Actual
- Fase: Spec 001 - Tarea T3 completada.
- Modelos acordados: Cloudflare/clef-flash (local, 4-bit NF4) y Google Gemini 2.5 Flash (Cloud, AI Studio).
- T1 (Schemas y Contratos): Implementados en `backend/app/schemas.py` con 24 tests unitarios pasando en verde en `backend/tests/test_schemas.py`.
- T2 (Servicio Clef-Flash Local): Implementado en `backend/app/services/clef_service.py` con 3 tests pasando en verde en `backend/tests/test_clef_service.py`.
- T3 (Servicio Cloud Gemini 2.5 Flash): Implementado en `backend/app/services/gemini_service.py` con SDK oficial `google-genai` (v2.28.0) y 10 tests unitarios/mock pasando en verde en `backend/tests/test_gemini_service.py` (más 1 test condicional de integración real omitido en ausencia de API Key).

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

## Errores a Evitar
- No cargar modelos en FP16 en la RTX 4060 (provoca Out Of Memory).
- Evitar usar el Python 3.14 global del sistema por inconsistencia de `pydantic-core` en paquetes rolling de CachyOS; usar siempre el entorno virtual en `backend/.venv`.
- No intentar instanciar `AutoProcessor` para tareas de solo texto de Clef-Flash si torchvision no está compilado, ya que el video processor exige `torchvision`; usar `AutoTokenizer` directamente.