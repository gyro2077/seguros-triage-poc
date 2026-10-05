# Constitución del Sistema de Triage
Principios innegociables. Toda spec, plan y código debe cumplirlos estrictamente.

1. **Separación Estricta (Decoupled Architecture)**: El backend (FastAPI) gestiona exclusivamente la inferencia de modelos y contratos tipados. El frontend (React/Vite) solo consume APIs REST y renderiza estados.
2. **La Spec Manda**: Prohibido implementar código que no esté especificado en `spec.md` y desglosado en `tasks.md`.
3. **Cero Vibe-Coding / Tipado Fuerte**: Todo endpoint debe definir esquemas Pydantic en backend e interfaces TypeScript en frontend.
4. **Respeto a los Límites de Hardware**: `clef-flash` debe correr obligatoriamente cuantizado (4-bit) para no sobrepasar los 6.5 GB de VRAM en la GPU de 8GB.
5. **Transparencia en la Comparativa**: No mezclar métricas de nube con métricas locales. Si se compara costo, debe indicarse la fórmula exacta basada en tokens consumidos por Gemini vs costo marginal cero en Clef.
6. **Idioma**: Código y nombres técnicos en inglés; interfaz y documentación de negocio en español.