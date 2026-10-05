# MEMORY.md - Bitácora de Estado
## Estado Actual
- Fase: Spec 001 - Tarea T1 completada.
- Modelos acordados: Cloudflare/clef-flash (local, 4-bit) y Google Gemini 2.5 Flash (Cloud, AI Studio).
- T1 (Schemas y Contratos): Implementados en `backend/app/schemas.py` con 24 tests unitarios pasando en verde en `backend/tests/test_schemas.py`.

## Decisiones Técnicas
- Se descarta Streamlit por falta de control sobre micro-latencias y diseño visual corporativo.
- Frontend se desarrollará con React + Tailwind para permitir visualizaciones paralelas con streaming real.
- Backend configurado con virtualenv Python 3.11.15 (`backend/.venv`) vía `uv` para garantizar compatibilidad estricta con Pydantic v2 y futuros frameworks de inferencia (PyTorch/Transformers) en CachyOS.
- Modelos Pydantic incluyen validación cruzada actuarial estricta: consistencia entre Macro-Ramo y Ramo Específico, validación de catálogos cerrados y rangos de severidad con mapeo SLA Jira.

## Errores a Evitar
- No cargar modelos en FP16 en la RTX 4060 (provoca Out Of Memory).
- Evitar usar el Python 3.14 global del sistema por inconsistencia de `pydantic-core` en paquetes rolling de CachyOS; usar siempre el entorno virtual en `backend/.venv`.