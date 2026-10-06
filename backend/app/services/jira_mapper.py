"""Jira Service Management issue payload mapper for actuarial triage decisions (T4).

Maps a ``TriageDecision`` into a single or linked dual-ticket ``JiraTicketSet``
following Ecuadorian insurance regulations and SLA priorities.
"""

from __future__ import annotations

from typing import Optional

from app.schemas import (
    RAMOS_GENERALES,
    RAMOS_VIDA_PERSONAS,
    SEVERITY_PRIORITY_LABELS,
    SEVERITY_SLA_HOURS,
    JiraIssuePayload,
    JiraTicketSet,
    MacroRamo,
    RamoEspecifico,
    TriageDecision,
)


def map_decision_to_jira(
    decision: TriageDecision,
    incident_text: Optional[str] = None,
    project_key: str = "SIN",
) -> JiraTicketSet:
    """Transform an actuarial TriageDecision into a JiraTicketSet."""
    priority_label = SEVERITY_PRIORITY_LABELS[decision.severidad]
    sla_hours = SEVERITY_SLA_HOURS[decision.severidad]

    # Dual ticket criteria: P1 (critical emergency) or MIXTO (crosses property and life/health)
    is_dual = decision.severidad == 1 or decision.macro_ramo == MacroRamo.MIXTO

    if not is_dual:
        # Standard Single Ticket
        summary = f"Siniestro [{decision.ramo_especifico.value}] - {priority_label}"
        primary = JiraIssuePayload(
            project_key=project_key,
            issue_type="Siniestro",
            summary=summary,
            description=incident_text,
            components=[decision.ramo_especifico.value],
            priority=priority_label,
            sla_hours=sla_hours,
            linked_issues=[],
        )
        return JiraTicketSet(
            primary_ticket=primary,
            secondary_ticket=None,
            is_dual_ticket=False,
        )

    # Dual Tickets (Patrimonial + Personas)
    if decision.macro_ramo == MacroRamo.MIXTO:
        if decision.ramo_especifico in RAMOS_GENERALES:
            patrimonial_ramo = decision.ramo_especifico
            personas_ramo = decision.ramo_secundario or RamoEspecifico.ASISTENCIA_MEDICA_SALUD
        else:
            patrimonial_ramo = decision.ramo_secundario or RamoEspecifico.VEHICULOS
            personas_ramo = decision.ramo_especifico
    else:
        # Severidad 1 (P1) en macro-ramo no mixto
        if decision.macro_ramo == MacroRamo.GENERALES:
            patrimonial_ramo = decision.ramo_especifico
            personas_ramo = (
                RamoEspecifico.ACCIDENTES_PERSONALES
                if decision.indicio_lesiones_corporales
                else RamoEspecifico.ASISTENCIA_MEDICA_SALUD
            )
        else:
            personas_ramo = decision.ramo_especifico
            patrimonial_ramo = (
                RamoEspecifico.RESPONSABILIDAD_CIVIL
                if decision.involucra_terceros
                else RamoEspecifico.VEHICULOS
            )

    # Primary ticket: Patrimonial
    primary_summary = f"Siniestro Patrimonial [{patrimonial_ramo.value}] - {priority_label}"
    sec_key_ref = f"{project_key}-PERSONAS-LINK"
    primary_ticket = JiraIssuePayload(
        project_key=project_key,
        issue_type="Siniestro",
        summary=primary_summary,
        description=incident_text,
        components=[patrimonial_ramo.value],
        priority=priority_label,
        sla_hours=sla_hours,
        linked_issues=[sec_key_ref],
    )

    # Secondary ticket: Personas (SLA prioritario)
    personas_priority = (
        "P1 - Crítico"
        if (decision.severidad == 1 or decision.indicio_lesiones_corporales)
        else SEVERITY_PRIORITY_LABELS[min(decision.severidad, 2)]
    )
    personas_sla = (
        SEVERITY_SLA_HOURS[1]
        if (decision.severidad == 1 or decision.indicio_lesiones_corporales)
        else SEVERITY_SLA_HOURS[min(decision.severidad, 2)]
    )
    secondary_summary = f"Siniestro Personas [{personas_ramo.value}] - {personas_priority}"
    prim_key_ref = f"{project_key}-PATRIMONIAL-LINK"
    secondary_ticket = JiraIssuePayload(
        project_key=project_key,
        issue_type="Siniestro",
        summary=secondary_summary,
        description=incident_text,
        components=[personas_ramo.value],
        priority=personas_priority,
        sla_hours=personas_sla,
        linked_issues=[prim_key_ref],
    )

    return JiraTicketSet(
        primary_ticket=primary_ticket,
        secondary_ticket=secondary_ticket,
        is_dual_ticket=True,
    )


class JiraMapper:
    """Service wrapper for Jira issue generation."""

    def __init__(self, project_key: str = "SIN") -> None:
        self._project_key = project_key

    def map(self, decision: TriageDecision, incident_text: Optional[str] = None) -> JiraTicketSet:
        return map_decision_to_jira(
            decision,
            incident_text=incident_text,
            project_key=self._project_key,
        )


_mapper: Optional[JiraMapper] = None


def get_jira_mapper() -> JiraMapper:
    """Process-wide singleton accessor."""
    global _mapper
    if _mapper is None:
        _mapper = JiraMapper()
    return _mapper
