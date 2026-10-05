# MEMORY.md - Bitácora de Estado
## Estado Actual
- Fase: Inicio de Spec 001. Estructura base inicializada.
- Modelos acordados: Cloudflare/clef-flash (local, 4-bit) y Google Gemini 2.5 Flash (Cloud, AI Studio).

## Decisiones Técnicas
- Se descarta Streamlit por falta de control sobre micro-latencias y diseño visual corporativo.
- Frontend se desarrollará con React + Tailwind para permitir visualizaciones paralelas con streaming real.

## Errores a Evitar
- No cargar modelos en FP16 en la RTX 4060 (provoca Out Of Memory).