/**
 * TypeScript domain contracts matching backend/app/schemas.py Pydantic models.
 * Follows Ecuadorian insurance regulations (Superintendencia de Compañías, Valores y Seguros).
 */

export type MacroRamo = 'GENERALES' | 'VIDA_Y_PERSONAS' | 'MIXTO';

export type RamoGenerales =
  | 'VEHICULOS'
  | 'TODO_RIESGO_CONTRATISTA_MONTAJE'
  | 'INCENDIO_LINEAS_ALIADAS'
  | 'TRANSPORTE_CARGA'
  | 'RESPONSABILIDAD_CIVIL'
  | 'FIANZAS_GARANTIAS'
  | 'ROTURA_MAQUINARIA';

export type RamoVidaPersonas =
  | 'ASISTENCIA_MEDICA_SALUD'
  | 'ACCIDENTES_PERSONALES'
  | 'VIDA_INDIVIDUAL_O_COLECTIVO'
  | 'EXEQUIAS_SEPELIO';

export type RamoEspecifico = RamoGenerales | RamoVidaPersonas;

export type Severidad = 1 | 2 | 3 | 4;

export interface TriageRequest {
  incident_text: string;
}

export interface TriageDecision {
  macro_ramo: MacroRamo;
  ramo_especifico: RamoEspecifico;
  involucra_terceros: boolean;
  indicio_lesiones_corporales: boolean;
  severidad: Severidad;
  requiere_revision_pericial?: boolean;
  ramo_secundario?: RamoEspecifico | null;
}

export interface JiraIssuePayload {
  project_key: string;
  issue_type: string;
  summary: string;
  description?: string | null;
  components: string[];
  priority: string;
  sla_hours: number;
  linked_issues?: string[];
}

export interface JiraTicketSet {
  primary_ticket: JiraIssuePayload;
  secondary_ticket?: JiraIssuePayload | null;
  is_dual_ticket: boolean;
}

export interface ModelExecutionMetrics {
  latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  projected_cost_100k_usd: number;
  vram_allocated_mb?: number | null;
}

export interface ModelTriageResult {
  model_name: string;
  success: boolean;
  schema_valid: boolean;
  decision?: TriageDecision | null;
  jira_tickets?: JiraTicketSet | null;
  metrics: ModelExecutionMetrics;
  error_message?: string | null;
}

export interface TriageComparisonResponse {
  incident_id: string;
  incident_text: string;
  clef_result: ModelTriageResult;
  gemini_result: ModelTriageResult;
  discrepancy_detected: boolean;
  cost_delta_projected_100k_usd: number;
}

export interface HealthResponse {
  status: string;
  gpu_available: boolean;
  gpu_name?: string | null;
  clef_loaded: boolean;
  gemini_model: string;
}
