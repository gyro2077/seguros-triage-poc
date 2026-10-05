# Plan Técnico: Spec 001
Arquitectura desacoplada: Backend FastAPI (Inferencia local + Cloud) y Frontend React + Vite.

## 1. Responsabilidad de Componentes

### Backend (`/backend`)
- `app/schemas.py`: Modelos Pydantic estrictos para peticiones, respuestas tipadas y esquemas de Jira.
- `app/services/clef_service.py`: Carga y ejecución de `Cloudflare/clef-flash` cuantizado (AWQ/GGUF/BitsAndBytes 4-bit) usando la API de decisión estructurada.
- `app/services/gemini_service.py`: Cliente de Google GenAI SDK configurado con el modelo `gemini-2.5-flash` y modo JSON estructurado.
- `app/services/jira_mapper.py`: Transforma la decisión actuarial en la carga JSON exacta de creación de issues en Jira Service Management.
- `app/main.py`: Endpoints REST `/api/triage/compare` y `/api/health`.

### Frontend (`/frontend`)
- React 19 + Vite + Tailwind CSS.
- Componentes:
  * `ClaimInput.tsx`: Selector de plantillas de siniestros preconfiguradas y campo de texto libre.
  * `ModelComparisonCard.tsx`: Tarjetas espejo para Clef vs Gemini destacando Latencia (ms), Tokens y Schema Integrity.
  * `JiraTicketPreview.tsx`: Vista previa del ticket Jira resultante (Macro-Ramo, Componente, SLA, Asignación).
  * `CostSimulator.tsx`: Proyección matemática dinámica para 100k incidentes.

## 2. Contratos de API (Interfaces Pydantic / TypeScript)

```python
class TriageRequest(BaseModel):
    incident_text: str = Field(..., min_length=15)

class TriageDecision(BaseModel):
    macro_ramo: Literal["GENERALES", "VIDA_Y_PERSONAS", "MIXTO"]
    ramo_especifico: str
    involucra_terceros: bool
    indicio_lesiones_corporales: bool
    severidad: int = Field(..., ge=1, le=4)

class JiraIssuePayload(BaseModel):
    project_key: str
    issue_type: str
    summary: str
    components: list[str]
    priority: str
    sla_hours: int