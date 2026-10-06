"""Unit tests for domain schemas and actuarial taxonomy contracts."""

import pytest
from pydantic import ValidationError

from app.schemas import (
    MacroRamo,
    RamoGenerales,
    RamoVidaPersonas,
    RamoEspecifico,
    RAMOS_GENERALES,
    RAMOS_VIDA_PERSONAS,
    SEVERITY_SLA_HOURS,
    SEVERITY_PRIORITY_LABELS,
    TriageRequest,
    TriageDecision,
    JiraIssuePayload,
    JiraTicketSet,
    ModelExecutionMetrics,
    ModelTriageResult,
    TriageComparisonResponse,
)


class TestTriageRequestSchema:
    """Test validation rules on TriageRequest input schema."""

    def test_valid_incident_text(self):
        valid_text = "Colisión frontal entre dos vehículos livianos en la Av. Simón Bolívar con daños severos."
        req = TriageRequest(incident_text=valid_text)
        assert req.incident_text == valid_text

    def test_incident_text_too_short_raises_validation_error(self):
        short_text = "Choque leve"  # 11 characters < 15
        with pytest.raises(ValidationError) as exc_info:
            TriageRequest(incident_text=short_text)
        errors = exc_info.value.errors()
        assert any(e["type"] == "string_too_short" for e in errors)

    def test_empty_incident_text_raises_validation_error(self):
        with pytest.raises(ValidationError):
            TriageRequest(incident_text="")


class TestActuarialTaxonomyEnums:
    """Test full coverage of closed catalog enums and actuarial branches."""

    def test_all_ramos_generales_present_in_catalog(self):
        expected_generales = {
            "VEHICULOS",
            "TODO_RIESGO_CONTRATISTA_MONTAJE",
            "INCENDIO_LINEAS_ALIADAS",
            "TRANSPORTE_CARGA",
            "RESPONSABILIDAD_CIVIL",
            "FIANZAS_GARANTIAS",
            "ROTURA_MAQUINARIA",
        }
        enum_generales_names = {r.name for r in RamoGenerales}
        assert enum_generales_names == expected_generales

        # Verify mapping in unified RamoEspecifico and RAMOS_GENERALES set
        for ramo_name in expected_generales:
            spec_enum = RamoEspecifico(ramo_name)
            assert spec_enum in RAMOS_GENERALES

    def test_all_ramos_vida_personas_present_in_catalog(self):
        expected_vida_personas = {
            "ASISTENCIA_MEDICA_SALUD",
            "ACCIDENTES_PERSONALES",
            "VIDA_INDIVIDUAL_O_COLECTIVO",
            "EXEQUIAS_SEPELIO",
        }
        enum_vida_names = {r.name for r in RamoVidaPersonas}
        assert enum_vida_names == expected_vida_personas

        # Verify mapping in unified RamoEspecifico and RAMOS_VIDA_PERSONAS set
        for ramo_name in expected_vida_personas:
            spec_enum = RamoEspecifico(ramo_name)
            assert spec_enum in RAMOS_VIDA_PERSONAS

    def test_invalid_ramo_enum_raises_error(self):
        with pytest.raises(ValueError):
            RamoEspecifico("RAMO_INVENTADO_NO_REGULADO")

    def test_invalid_macro_ramo_enum_raises_error(self):
        with pytest.raises(ValueError):
            MacroRamo("AEROESPACIAL")


class TestTriageDecisionValidation:
    """Test actuarial cross-validation and consistency checks in TriageDecision."""

    def test_valid_generales_decision_serialization(self):
        for ramo in RAMOS_GENERALES:
            decision = TriageDecision(
                macro_ramo=MacroRamo.GENERALES,
                ramo_especifico=ramo,
                involucra_terceros=True,
                indicio_lesiones_corporales=False,
                severidad=3,
            )
            assert decision.macro_ramo == MacroRamo.GENERALES
            assert decision.ramo_especifico == ramo
            data = decision.model_dump()
            assert data["ramo_especifico"] == ramo.value

    def test_valid_vida_personas_decision_serialization(self):
        for ramo in RAMOS_VIDA_PERSONAS:
            decision = TriageDecision(
                macro_ramo=MacroRamo.VIDA_Y_PERSONAS,
                ramo_especifico=ramo,
                involucra_terceros=False,
                indicio_lesiones_corporales=True,
                severidad=1,
            )
            assert decision.macro_ramo == MacroRamo.VIDA_Y_PERSONAS
            assert decision.ramo_especifico == ramo

    def test_generales_with_vida_branch_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            TriageDecision(
                macro_ramo=MacroRamo.GENERALES,
                ramo_especifico=RamoEspecifico.ASISTENCIA_MEDICA_SALUD,
                severidad=2,
            )
        assert "does not belong to MacroRamo GENERALES" in str(exc_info.value)

    def test_vida_personas_with_generales_branch_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            TriageDecision(
                macro_ramo=MacroRamo.VIDA_Y_PERSONAS,
                ramo_especifico=RamoEspecifico.VEHICULOS,
                severidad=3,
            )
        assert "does not belong to MacroRamo VIDA_Y_PERSONAS" in str(exc_info.value)

    def test_mixto_decision_with_cross_branches_valid(self):
        decision = TriageDecision(
            macro_ramo=MacroRamo.MIXTO,
            ramo_especifico=RamoEspecifico.VEHICULOS,
            ramo_secundario=RamoEspecifico.ACCIDENTES_PERSONALES,
            involucra_terceros=True,
            indicio_lesiones_corporales=True,
            severidad=1,
        )
        assert decision.macro_ramo == MacroRamo.MIXTO
        assert decision.ramo_especifico == RamoEspecifico.VEHICULOS
        assert decision.ramo_secundario == RamoEspecifico.ACCIDENTES_PERSONALES

    def test_mixto_decision_with_same_category_secondary_branch_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            TriageDecision(
                macro_ramo=MacroRamo.MIXTO,
                ramo_especifico=RamoEspecifico.VEHICULOS,
                ramo_secundario=RamoEspecifico.TRANSPORTE_CARGA,  # Both are Generales!
                severidad=2,
            )
        assert "must span across both Generales and Vida/Personas" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_sev", [0, 5, -1, 10])
    def test_invalid_severity_raises_validation_error(self, invalid_sev):
        with pytest.raises(ValidationError):
            TriageDecision(
                macro_ramo=MacroRamo.GENERALES,
                ramo_especifico=RamoEspecifico.VEHICULOS,
                severidad=invalid_sev,
            )

    @pytest.mark.parametrize(
        "severity, expected_sla, expected_label",
        [
            (1, 2, "P1 - Crítico"),
            (2, 6, "P2 - Alto"),
            (3, 24, "P3 - Medio"),
            (4, 48, "P4 - Bajo"),
        ],
    )
    def test_severity_sla_and_label_mappings(self, severity, expected_sla, expected_label):
        assert SEVERITY_SLA_HOURS[severity] == expected_sla
        assert SEVERITY_PRIORITY_LABELS[severity] == expected_label


class TestJiraSchemas:
    """Test Jira issue payloads and linked ticket schemas."""

    def test_jira_issue_payload_defaults_and_serialization(self):
        payload = JiraIssuePayload(
            summary="Siniestro Vehicular - Colisión Av. Occidental",
            components=["VEHICULOS"],
            priority="P3 - Medio",
            sla_hours=24,
        )
        assert payload.project_key == "SIN"
        assert payload.issue_type == "Siniestro"
        assert payload.sla_hours == 24
        assert payload.components == ["VEHICULOS"]

        serialized = payload.model_dump()
        assert serialized["summary"] == "Siniestro Vehicular - Colisión Av. Occidental"

    def test_jira_ticket_set_dual_tickets(self):
        primary = JiraIssuePayload(
            summary="Sub-ticket Patrimonial: Daño a bus interprovincial",
            components=["VEHICULOS"],
            priority="P1 - Crítico",
            sla_hours=2,
        )
        secondary = JiraIssuePayload(
            summary="Sub-ticket Médico: Asistencia médica para pasajeros lesionados",
            components=["ASISTENCIA_MEDICA_SALUD"],
            priority="P1 - Crítico",
            sla_hours=2,
            linked_issues=["SIN-101"],
        )
        ticket_set = JiraTicketSet(
            primary_ticket=primary,
            secondary_ticket=secondary,
            is_dual_ticket=True,
        )
        assert ticket_set.is_dual_ticket is True
        assert ticket_set.secondary_ticket is not None
        assert "ASISTENCIA_MEDICA_SALUD" in ticket_set.secondary_ticket.components


class TestComparisonResponseSchemas:
    """Test metrics and comparative benchmark response payload contracts."""

    def test_model_execution_metrics_and_comparison_response(self):
        metrics_clef = ModelExecutionMetrics(
            latency_ms=84.5,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost_usd=0.0,
            projected_cost_100k_usd=0.0,
            vram_allocated_mb=4200.0,
        )
        metrics_gemini = ModelExecutionMetrics(
            latency_ms=950.2,
            prompt_tokens=220,
            completion_tokens=48,
            total_tokens=268,
            estimated_cost_usd=0.00015,
            projected_cost_100k_usd=15.0,
        )

        clef_res = ModelTriageResult(
            model_name="clef-flash",
            success=True,
            schema_valid=True,
            metrics=metrics_clef,
        )
        gemini_res = ModelTriageResult(
            model_name="gemini-3.8-flash",
            success=True,
            schema_valid=True,
            metrics=metrics_gemini,
        )

        comparison = TriageComparisonResponse(
            incident_id="incident-uuid-1234",
            incident_text="Choque frontal en autopista con derrame de combustible.",
            clef_result=clef_res,
            gemini_result=gemini_res,
            discrepancy_detected=False,
            cost_delta_projected_100k_usd=15.0,
        )

        data = comparison.model_dump()
        assert data["incident_id"] == "incident-uuid-1234"
        assert data["clef_result"]["metrics"]["latency_ms"] == 84.5
        assert data["gemini_result"]["metrics"]["total_tokens"] == 268
