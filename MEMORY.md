# MEMORY.md - Bitácora de Estado
## Estado Actual
- Fase: Spec 001 - Tarea T2 completada.
- Modelos acordados: Cloudflare/clef-flash (local, 4-bit NF4) y Google Gemini 2.5 Flash (Cloud, AI Studio).
- T1 (Schemas y Contratos): Implementados en `backend/app/schemas.py` con 24 tests unitarios pasando en verde en `backend/tests/test_schemas.py`.
- T2 (Servicio Clef-Flash Local): Implementado en `backend/app/services/clef_service.py` con 3 tests pasando en verde en `backend/tests/test_clef_service.py`.

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
- En `clef_service.py`, se distribuye el modelo mediante `device_map` colocando la torre visual (`model.visual`), `embed_tokens` y la matriz léxica `lm_head` en CPU, mientras las 32 capas transformadoras del lenguaje corren en GPU con cuantización NF4 4-bit de BitsAndBytes. Esto garantiza no sobrepasar los 8 GB de VRAM de la RTX 4060 sin penalizar la evaluación del Joint Schema Head.

## Errores a Evitar
- No cargar modelos en FP16 en la RTX 4060 (provoca Out Of Memory).
- Evitar usar el Python 3.14 global del sistema por inconsistencia de `pydantic-core` en paquetes rolling de CachyOS; usar siempre el entorno virtual en `backend/.venv`.
- No intentar instanciar `AutoProcessor` para tareas de solo texto de Clef-Flash si torchvision no está compilado, ya que el video processor exige `torchvision`; usar `AutoTokenizer` directamente.