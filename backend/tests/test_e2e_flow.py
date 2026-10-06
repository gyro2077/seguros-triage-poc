"""End-to-end integration and requirement verification tests (T6 / Step 7 SDD).

Audits all functional requirements (RF-1 through RF-6) and cross-flows:
- Colapso grúa torre (MIXTO / P1 -> Dual Linked Jira Tickets)
- Choque vehicular leve (GENERALES / P3-P4 -> Single Jira Ticket)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import (
    MacroRamo,
    ModelExecutionMetrics,
    RamoEspecifico,
    TriageComparisonResponse,
    TriageDecision,
)
from app.services.gemini_service import GeminiTriageResult
from app.services.jira_mapper import map_decision_to_jira

client = TestClient(app)

GRUA_COLAPSO_TEXT = (
    "Durante trabajos de izaje en la construcción del viaducto en la Av. Simón Bolívar (Quito), "
    "una grúa telescópica de 45 toneladas sufrió el colapso de su pluma principal. La estructura cayó "
    "sobre dos vehículos de terceros estacionados y causó heridas graves con politraumatismo al operador "
    "y a un obrero cercano, quienes fueron evacuados de urgencia al Hospital Eugenio Espejo."
)

CHOQUE_LEVE_TEXT = (
    "Colisión por alcance a baja velocidad en el sector La Pradera, Guayaquil. El vehículo asegurado rozó "
    "el guardafango posterior de un sedán particular en el semáforo. Únicamente se evidencia raspón superficial "
    "de pintura y hendidura menor sin personas lesionadas ni activación de airbags."
)


class TestCrossFlowRequirements:
    """Validates specific claim scenarios and dual vs single ticket generation."""

    def test_grua_colapso_dual_ticket_flow(self) -> None:
        """Case 'Colapso grúa mixto': Must generate dual linked Jira tickets."""
        decision = TriageDecision(
            macro_ramo=MacroRamo.MIXTO,
            ramo_especifico=RamoEspecifico.TODO_RIESGO_CONTRATISTA_MONTAJE,
            ramo_secundario=RamoEspecifico.ASISTENCIA_MEDICA_SALUD,
            severidad=1,
            involucra_terceros=True,
            indicio_lesiones_corporales=True,
            requiere_revision_pericial=True,
        )

        ticket_set = map_decision_to_jira(decision, incident_text=GRUA_COLAPSO_TEXT)

        # Must be dual ticket
        assert ticket_set.is_dual_ticket is True
        assert ticket_set.secondary_ticket is not None

        # Ticket A (Patrimonial)
        patrimonial = ticket_set.primary_ticket
        assert patrimonial.components == [RamoEspecifico.TODO_RIESGO_CONTRATISTA_MONTAJE.value]
        assert patrimonial.priority == "P1 - Crítico"
        assert patrimonial.sla_hours == 2
        assert len(patrimonial.linked_issues) > 0

        # Ticket B (Personas)
        personas = ticket_set.secondary_ticket
        assert personas.components == [RamoEspecifico.ASISTENCIA_MEDICA_SALUD.value]
        assert personas.priority == "P1 - Crítico"
        assert personas.sla_hours == 2
        assert len(personas.linked_issues) > 0

    def test_choque_vehicular_leve_single_ticket_flow(self) -> None:
        """Case 'Choque vehicular leve': Must generate single P3 ticket with 24h SLA."""
        decision = TriageDecision(
            macro_ramo=MacroRamo.GENERALES,
            ramo_especifico=RamoEspecifico.VEHICULOS,
            severidad=3,
            involucra_terceros=True,
            indicio_lesiones_corporales=False,
            requiere_revision_pericial=False,
        )

        ticket_set = map_decision_to_jira(decision, incident_text=CHOQUE_LEVE_TEXT)

        assert ticket_set.is_dual_ticket is False
        assert ticket_set.secondary_ticket is None

        primary = ticket_set.primary_ticket
        assert primary.components == [RamoEspecifico.VEHICULOS.value]
        assert primary.priority == "P3 - Medio"
        assert primary.sla_hours == 24
        assert primary.linked_issues == []


class TestAuditRequirementsRF1ToRF6:
    """Formally audits RF-1 through RF-6 via end-to-end mock execution."""

    @patch("app.main.get_clef_service")
    @patch("app.main.get_gemini_service")
    def test_rf1_to_rf6_compliance(
        self,
        mock_get_gemini: MagicMock,
        mock_get_clef: MagicMock,
    ) -> None:
        # Mock Clef (RF-2: Forward pass output)
        mock_clef = MagicMock()
        mock_clef.triage.return_value = TriageDecision(
            macro_ramo=MacroRamo.MIXTO,
            ramo_especifico=RamoEspecifico.TODO_RIESGO_CONTRATISTA_MONTAJE,
            ramo_secundario=RamoEspecifico.ASISTENCIA_MEDICA_SALUD,
            severidad=1,
            involucra_terceros=True,
            indicio_lesiones_corporales=True,
        )
        mock_clef.vram_allocated_bytes.return_value = 3_800_000_000
        mock_get_clef.return_value = mock_clef

        # Mock Gemini (RF-3: Structured output + Token counts + Latency)
        mock_gemini = MagicMock()
        mock_gemini.model_name = "gemini-2.5-flash"
        mock_gemini.triage.return_value = GeminiTriageResult(
            decision=TriageDecision(
                macro_ramo=MacroRamo.MIXTO,
                ramo_especifico=RamoEspecifico.TODO_RIESGO_CONTRATISTA_MONTAJE,
                ramo_secundario=RamoEspecifico.ASISTENCIA_MEDICA_SALUD,
                severidad=1,
                involucra_terceros=True,
                indicio_lesiones_corporales=True,
            ),
            metrics=ModelExecutionMetrics(
                latency_ms=780.0,
                prompt_tokens=220,
                completion_tokens=65,
                total_tokens=285,
                estimated_cost_usd=0.000036,
                projected_cost_100k_usd=3.60,
            ),
        )
        mock_get_gemini.return_value = mock_gemini

        # RF-1: Parallel execution on POST /api/triage/compare
        response = client.post("/api/triage/compare", json={"incident_text": GRUA_COLAPSO_TEXT})
        assert response.status_code == 200

        data = response.json()
        validated = TriageComparisonResponse.model_validate(data)

        # RF-2 Audit: Clef structured payload
        assert validated.clef_result.model_name == "clef-flash"
        assert validated.clef_result.decision is not None
        assert validated.clef_result.decision.macro_ramo == MacroRamo.MIXTO
        assert validated.clef_result.metrics.latency_ms > 0

        # RF-3 Audit: Gemini telemetry
        assert validated.gemini_result.metrics.prompt_tokens == 220
        assert validated.gemini_result.metrics.completion_tokens == 65
        assert validated.gemini_result.metrics.latency_ms == 780.0

        # RF-5 Audit: Dual Jira tickets on MIXTO / P1
        assert validated.clef_result.jira_tickets is not None
        assert validated.clef_result.jira_tickets.is_dual_ticket is True
        assert validated.gemini_result.jira_tickets is not None
        assert validated.gemini_result.jira_tickets.is_dual_ticket is True

        # RF-6 Audit: Projected cost difference for 100k claims
        assert validated.cost_delta_projected_100k_usd == pytest.approx(3.60, abs=0.1)

    @patch("app.main.get_clef_service")
    @patch("app.main.get_gemini_service")
    def test_rf4_schema_failure_isolation(
        self,
        mock_get_gemini: MagicMock,
        mock_get_clef: MagicMock,
    ) -> None:
        """RF-4: Gemini schema error does not disrupt Clef-Flash execution."""
        mock_clef = MagicMock()
        mock_clef.triage.return_value = TriageDecision(
            macro_ramo=MacroRamo.GENERALES,
            ramo_especifico=RamoEspecifico.VEHICULOS,
            severidad=3,
        )
        mock_clef.vram_allocated_bytes.return_value = 0
        mock_get_clef.return_value = mock_clef

        mock_gemini = MagicMock()
        mock_gemini.model_name = "gemini-2.5-flash"
        mock_gemini.triage.side_effect = RuntimeError("Malformed JSON returned by LLM")
        mock_get_gemini.return_value = mock_gemini

        response = client.post("/api/triage/compare", json={"incident_text": CHOQUE_LEVE_TEXT})
        assert response.status_code == 200
        data = response.json()

        # Clef succeeded
        assert data["clef_result"]["success"] is True
        assert data["clef_result"]["schema_valid"] is True

        # Gemini flagged with error without crashing endpoint
        assert data["gemini_result"]["success"] is False
        assert data["gemini_result"]["schema_valid"] is False
        assert "Malformed JSON" in data["gemini_result"]["error_message"]
