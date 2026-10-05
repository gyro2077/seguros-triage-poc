# AGENTS.md - Motor de Triage de Siniestros (Clef vs Gemini)
Plataforma de comparación en tiempo real entre modelos de decisión System 1 (Clef-Flash local) y LLMs en la nube (Gemini 2.5 Flash).

## Stack y Estructura
- Backend: Python 3.11+, FastAPI, Uvicorn, Google GenAI SDK, PyTorch / Transformers (o vLLM/llama.cpp para clef-flash).
- Frontend: React 19, Vite, Tailwind CSS, Lucide-React.
- Entorno: CachyOS Linux, NVIDIA RTX 4060 (8GB VRAM).

## Comandos Principales
- Backend Run: `cd backend && uvicorn app.main:app --reload --port 8000`
- Backend Test: `cd backend && pytest`
- Frontend Run: `cd frontend && npm run dev`
- Frontend Build: `cd frontend && npm run build`

## Límites de Acción
- SIEMPRE: Leer `docs/constitution.md` y la spec activa antes de sugerir o implementar código.
- PREGUNTA ANTES: De instalar dependencias nuevas o alterar contratos de API en `backend/app/schemas.py`.
- NUNCA: Generar interfaces con Streamlit o mezclar código de frontend dentro del backend.

## Verificación
- Cada endpoint se valida con pytest antes de conectarlo al frontend.
- Cada vista se valida mediante Chrome DevTools MCP revisando la consola y el renderizado responsive.