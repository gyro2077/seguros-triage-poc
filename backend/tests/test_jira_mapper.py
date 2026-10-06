"""Unit tests for Jira Service Management mapper service (T4).

Validates SLA calculations, components, and dual-ticket generation for P1 and MIXTO claims.
"""

from __future__ import annotations

import pytest

from app.schemas import (
    MacroRamo,
    RamoEspecifico,
    TriageDecision,
)
from app.services.jira_mapper import (
    JiraMapper,
    map_decision_to_jira,
)


class TestJiraMapperSingleTickets:
    """Tests for single ticket generation on standard claims (non-P1, non-MIXTO)."""

    def test_single_ticket_generales_p3(self) -> None:
        decision = TriageDecision(
            macro_ramo=MacroRamo.GENERALES,
            ramo_especifico=RamoEspecifico.VEHICULOS,
            severidad=3,
            involucra_terceros=True,
            indicio_lesiones_corporales=False,
        )
        ticket_set = map_decision_to_jira(decision, incident_text="Golpe leve en retrovisor")

        assert ticket_set.is_dual_ticket is False
        assert ticket_set.secondary_ticket is None

        primary = ticket_set.primary_ticket
        assert primary.project_key == "SIN"
        assert primary.issue_type == "Siniestro"
        assert primary.components == [RamoEspecifico.VEHICULOS.value]
        assert primary.priority == "P3 - Medio"
        assert primary.sla_hours == 24
        assert primary.description == "Golpe leve en retrovisor"
        assert "VEHICULOS" in primary.summary
        assert primary.linked_issues == []

    def test_single_ticket_vida_p2(self) -> None:
        decision = TriageDecision(
            macro_ramo=MacroRamo.VIDA_Y_PERSONAS,
            ramo_especifico=RamoEspecifico.ASISTENCIA_MEDICA_SALUD,
            severidad=2,
            involucra_terceros=False,
            indicio_lesiones_corporales=True,
        )
        ticket_set = map_decision_to_jira(decision)

        assert ticket_set.is_dual_ticket is False
        assert ticket_set.secondary_ticket is None

        primary = ticket_set.primary_ticket
        assert primary.components == [RamoEspecifico.ASISTENCIA_MEDICA_SALUD.value]
        assert primary.priority == "P2 - Alto"
        assert primary.sla_hours == 6

    def test_single_ticket_p4(self) -> None:
        decision = TriageDecision(
            macro_ramo=MacroRamo.GENERALES,
            ramo_especifico=RamoEspecifico.ROTURA_MAQUINARIA,
            severidad=4,
        )
        ticket_set = map_decision_to_jira(decision)

        assert ticket_set.is_dual_ticket is False
        assert ticket_set.primary_ticket.priority == "P4 - Bajo"
        assert ticket_set.primary_ticket.sla_hours == 48


class TestJiraMapperDualTickets:
    """Tests for dual ticket generation on P1 (critical) or MIXTO claims."""

    def test_dual_ticket_on_severity_1_generales(self) -> None:
        """P1 severity on GENERALES generates linked Patrimonial and Personas tickets."""
        decision = TriageDecision(
            macro_ramo=MacroRamo.GENERALES,
            ramo_especifico=RamoEspecifico.VEHICULOS,
            severidad=1,
            involucra_terceros=True,
            indicio_lesiones_corporales=True,
        )
        ticket_set = map_decision_to_jira(decision, incident_text="Colisión frontal con heridos graves")

        assert ticket_set.is_dual_ticket is True
        assert ticket_set.secondary_ticket is not None

        primary = ticket_set.primary_ticket
        secondary = ticket_set.secondary_ticket

        # Ticket A: Patrimonial
        assert primary.components == [RamoEspecifico.VEHICULOS.value]
        assert primary.priority == "P1 - Crítico"
        assert primary.sla_hours == 2
        assert len(primary.linked_issues) > 0

        # Ticket B: Personas
        assert primary.linked_issues[0] in secondary.summary or len(secondary.linked_issues) > 0
        assert secondary.priority == "P1 - Crítico"
        assert secondary.sla_hours == 2
        assert any(
            c in [RamoEspecifico.ACCIDENTES_PERSONALES.value, RamoEspecifico.ASISTENCIA_MEDICA_SALUD.value]
            for c in secondary.components
        )

    def test_dual_ticket_on_mixto_claim(self) -> None:
        """MIXTO claim generates linked Patrimonial and Personas tickets even at P2."""
        decision = TriageDecision(
            macro_ramo=MacroRamo.MIXTO,
            ramo_especifico=RamoEspecifico.VEHICULOS,
            ramo_secundario=RamoEspecifico.ASISTENCIA_MEDICA_SALUD,
            severidad=2,
            involucra_terceros=True,
            indicio_lesiones_corporales=True,
        )
        ticket_set = map_decision_to_jira(decision)

        assert ticket_set.is_dual_ticket is True
        assert ticket_set.secondary_ticket is not None

        primary = ticket_set.primary_ticket
        secondary = ticket_set.secondary_ticket

        assert primary.components == [RamoEspecifico.VEHICULOS.value]
        assert secondary.components == [RamoEspecifico.ASISTENCIA_MEDICA_SALUD.value]
        assert primary.sla_hours == 6
        assert secondary.sla_hours <= 6

    def test_class_wrapper_interface(self) -> None:
        """JiraMapper class instance wrapper produces identical results."""
        mapper = JiraMapper()
        decision = TriageDecision(
            macro_ramo=MacroRamo.GENERALES,
            ramo_especifico=RamoEspecifico.INCENDIO_LINEAS_ALIADAS,
            severidad=3,
        )
        ticket_set = mapper.map(decision)
        assert ticket_set.primary_ticket.components == [RamoEspecifico.INCENDIO_LINEAS_ALIADAS.value]
