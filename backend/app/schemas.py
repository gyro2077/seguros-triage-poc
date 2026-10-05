"""Domain schemas and contracts for insurance claims triage.

Follows the regulatory taxonomy of the Superintendencia de Compañías, Valores y Seguros
(Ecuadorian Insurance Framework) and Jira Service Management issue generation contracts.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class MacroRamo(str, Enum):
    """Macro-ramo actuarial categories."""
    GENERALES = "GENERALES"
    VIDA_Y_PERSONAS = "VIDA_Y_PERSONAS"
    MIXTO = "MIXTO"


class RamoGenerales(str, Enum):
    """Specific branches belonging to Ramos Generales."""
    VEHICULOS = "VEHICULOS"
    TODO_RIESGO_CONTRATISTA_MONTAJE = "TODO_RIESGO_CONTRATISTA_MONTAJE"
    INCENDIO_LINEAS_ALIADAS = "INCENDIO_LINEAS_ALIADAS"
    TRANSPORTE_CARGA = "TRANSPORTE_CARGA"
    RESPONSABILIDAD_CIVIL = "RESPONSABILIDAD_CIVIL"
    FIANZAS_GARANTIAS = "FIANZAS_GARANTIAS"
    ROTURA_MAQUINARIA = "ROTURA_MAQUINARIA"


class RamoVidaPersonas(str, Enum):
    """Specific branches belonging to Ramos Vida y Personas."""
    ASISTENCIA_MEDICA_SALUD = "ASISTENCIA_MEDICA_SALUD"
    ACCIDENTES_PERSONALES = "ACCIDENTES_PERSONALES"
    VIDA_INDIVIDUAL_O_COLECTIVO = "VIDA_INDIVIDUAL_O_COLECTIVO"
    EXEQUIAS_SEPELIO = "EXEQUIAS_SEPELIO"


class RamoEspecifico(str, Enum):
    """Closed catalog of all valid specific branches across General and Life/People."""
    # Generales
    VEHICULOS = "VEHICULOS"
    TODO_RIESGO_CONTRATISTA_MONTAJE = "TODO_RIESGO_CONTRATISTA_MONTAJE"
    INCENDIO_LINEAS_ALIADAS = "INCENDIO_LINEAS_ALIADAS"
    TRANSPORTE_CARGA = "TRANSPORTE_CARGA"
    RESPONSABILIDAD_CIVIL = "RESPONSABILIDAD_CIVIL"
    FIANZAS_GARANTIAS = "FIANZAS_GARANTIAS"
    ROTURA_MAQUINARIA = "ROTURA_MAQUINARIA"
    # Vida y Personas
    ASISTENCIA_MEDICA_SALUD = "ASISTENCIA_MEDICA_SALUD"
    ACCIDENTES_PERSONALES = "ACCIDENTES_PERSONALES"
    VIDA_INDIVIDUAL_O_COLECTIVO = "VIDA_INDIVIDUAL_O_COLECTIVO"
    EXEQUIAS_SEPELIO = "EXEQUIAS_SEPELIO"


# Regulatory categorization sets
RAMOS_GENERALES: set[RamoEspecifico] = {
    RamoEspecifico.VEHICULOS,
    RamoEspecifico.TODO_RIESGO_CONTRATISTA_MONTAJE,
    RamoEspecifico.INCENDIO_LINEAS_ALIADAS,
    RamoEspecifico.TRANSPORTE_CARGA,
    RamoEspecifico.RESPONSABILIDAD_CIVIL,
    RamoEspecifico.FIANZAS_GARANTIAS,
    RamoEspecifico.ROTURA_MAQUINARIA,
}

RAMOS_VIDA_PERSONAS: set[RamoEspecifico] = {
    RamoEspecifico.ASISTENCIA_MEDICA_SALUD,
    RamoEspecifico.ACCIDENTES_PERSONALES,
    RamoEspecifico.VIDA_INDIVIDUAL_O_COLECTIVO,
    RamoEspecifico.EXEQUIAS_SEPELIO,
}

# SLA and Priority mappings according to regulatory severity
SEVERITY_SLA_HOURS: dict[int, int] = {
    1: 2,   # P1 - Crítico: < 2 horas
    2: 6,   # P2 - Alto: < 6 horas
    3: 24,  # P3 - Medio: < 24 horas
    4: 48,  # P4 - Bajo: < 48 horas
}

SEVERITY_PRIORITY_LABELS: dict[int, str] = {
    1: "P1 - Crítico",
    2: "P2 - Alto",
    3: "P3 - Medio",
    4: "P4 - Bajo",
}


class TriageRequest(BaseModel):
    """Input payload for insurance claims triage."""
    incident_text: str = Field(
        ...,
        min_length=15,
        description="Unstructured claim incident narrative text",
    )


class TriageDecision(BaseModel):
    """Actuarial decision output from triage classification models."""
    macro_ramo: MacroRamo
    ramo_especifico: RamoEspecifico
    involucra_terceros: bool = False
    indicio_lesiones_corporales: bool = False
    severidad: int = Field(
        ...,
        ge=1,
        le=4,
        description="Actuarial severity score (1: P1 Crítico, 2: P2 Alto, 3: P3 Medio, 4: P4 Bajo)",
    )
    requiere_revision_pericial: bool = Field(
        default=False,
        description="True if incident is ambiguous or requires manual expert assessment",
    )
    ramo_secundario: Optional[RamoEspecifico] = Field(
        default=None,
        description="Secondary branch for MIXTO claims (e.g. Property + Medical)",
    )

    @model_validator(mode="after")
    def validate_actuarial_consistency(self) -> "TriageDecision":
        """Ensure macro_ramo and ramo_especifico are consistent with actuarial regulations."""
        if self.macro_ramo == MacroRamo.GENERALES:
            if self.ramo_especifico not in RAMOS_GENERALES:
                raise ValueError(
                    f"Ramo '{self.ramo_especifico.value}' does not belong to MacroRamo GENERALES."
                )
        elif self.macro_ramo == MacroRamo.VIDA_Y_PERSONAS:
            if self.ramo_especifico not in RAMOS_VIDA_PERSONAS:
                raise ValueError(
                    f"Ramo '{self.ramo_especifico.value}' does not belong to MacroRamo VIDA_Y_PERSONAS."
                )
        elif self.macro_ramo == MacroRamo.MIXTO:
            # Mixto requires valid branches. If ramo_secundario is provided, they shouldn't both be from the exact same category
            if self.ramo_secundario is not None:
                is_prim_gen = self.ramo_especifico in RAMOS_GENERALES
                is_sec_gen = self.ramo_secundario in RAMOS_GENERALES
                if is_prim_gen == is_sec_gen:
                    raise ValueError(
                        "MIXTO claims with secondary branch must span across both Generales and Vida/Personas."
                    )
        return self


class JiraIssuePayload(BaseModel):
    """Standard payload structure for Jira Service Management incident creation."""
    project_key: str = Field(default="SIN", description="Jira project key")
    issue_type: str = Field(default="Siniestro", description="Issue type in Jira")
    summary: str = Field(..., description="Concise summary for Jira issue")
    description: Optional[str] = Field(default=None, description="Detailed incident narrative")
    components: List[str] = Field(default_factory=list, description="Affected components/branches")
    priority: str = Field(..., description="Priority label (e.g. P1 - Crítico)")
    sla_hours: int = Field(..., description="Maximum SLA hours")
    linked_issues: List[str] = Field(
        default_factory=list,
        description="Linked issue keys for dual tickets (e.g. in MIXTO or P1 claims)",
    )


class JiraTicketSet(BaseModel):
    """Set of generated Jira tickets, supporting single or linked dual-tickets."""
    primary_ticket: JiraIssuePayload
    secondary_ticket: Optional[JiraIssuePayload] = None
    is_dual_ticket: bool = False


class ModelExecutionMetrics(BaseModel):
    """Execution telemetry and cost metrics for inference benchmark."""
    latency_ms: float = Field(..., description="Execution latency in milliseconds")
    prompt_tokens: int = Field(default=0, description="Input tokens used (0 for local Clef)")
    completion_tokens: int = Field(default=0, description="Output tokens used (0 for local Clef)")
    total_tokens: int = Field(default=0, description="Total tokens consumed")
    estimated_cost_usd: float = Field(
        default=0.0,
        description="Marginal cost for this single transaction in USD",
    )
    projected_cost_100k_usd: float = Field(
        default=0.0,
        description="Projected cost for 100,000 requests in USD",
    )
    vram_allocated_mb: Optional[float] = Field(
        default=None,
        description="GPU VRAM memory allocated during inference (for local model)",
    )


class ModelTriageResult(BaseModel):
    """Comprehensive result of a single model's triage evaluation."""
    model_name: str = Field(..., description="Identifier of the model (e.g. clef-flash, gemini-2.5-flash)")
    success: bool = Field(default=True, description="Whether the inference succeeded")
    schema_valid: bool = Field(default=True, description="Whether output strictly adhered to the schema")
    decision: Optional[TriageDecision] = Field(default=None, description="Classified triage decision")
    jira_tickets: Optional[JiraTicketSet] = Field(default=None, description="Generated Jira ticket schemas")
    metrics: ModelExecutionMetrics
    error_message: Optional[str] = Field(default=None, description="Error or schema failure details")


class TriageComparisonResponse(BaseModel):
    """Parallel comparison response contract returned by the API."""
    incident_id: str = Field(..., description="Unique incident trace UUID")
    incident_text: str = Field(..., description="Original claim narrative")
    clef_result: ModelTriageResult
    gemini_result: ModelTriageResult
    discrepancy_detected: bool = Field(
        default=False,
        description="True if Clef and Gemini differed in macro-ramo or severity",
    )
    cost_delta_projected_100k_usd: float = Field(
        default=0.0,
        description="Cost difference projected at 100k requests/month",
    )
