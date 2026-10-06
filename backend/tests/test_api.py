"""Integration and endpoint tests for FastAPI Triage Engine (T4).

Uses FastAPI TestClient and mocked model services to validate concurrent execution,
health checks, schema integrity, and discrepancy detection.
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

client = TestClient(app)

SAMPLE_CLAIM_TEXT = (
    "Colisión múltiple entre tres vehículos en la Autopista General Rumiñahui. "
    "Dos conductores presentan lesiones cervicales y fueron trasladados a una casa de salud."
)


def _make_dummy_clef_decision() -> TriageDecision:
    return TriageDecision(
        macro_ramo=MacroRamo.GENERALES,
        ramo_especifico=RamoEspecifico.VEHICULOS,
        severidad=2,
        involucra_terceros=True,
        indicio_lesiones_corporales=True,
        requiere_revision_pericial=False,
    )


def _make_dummy_gemini_result() -> GeminiTriageResult:
    decision = TriageDecision(
        macro_ramo=MacroRamo.GENERALES,
        ramo_especifico=RamoEspecifico.VEHICULOS,
        severidad=2,
        involucra_terceros=True,
        indicio_lesiones_corporales=True,
        requiere_revision_pericial=False,
    )
    metrics = ModelExecutionMetrics(
        latency_ms=850.5,
        prompt_tokens=180,
        completion_tokens=45,
        total_tokens=225,
        estimated_cost_usd=0.000027,
        projected_cost_100k_usd=2.7,
    )
    return GeminiTriageResult(decision=decision, metrics=metrics)


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_check_returns_ok_and_metadata(self) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "gpu_available" in data
        assert "clef_loaded" in data
        assert "gemini_model" in data


class TestCompareEndpoint:
    """Tests for POST /api/triage/compare."""

    @patch("app.main.get_clef_service")
    @patch("app.main.get_gemini_service")
    def test_compare_endpoint_success(
        self,
        mock_get_gemini: MagicMock,
        mock_get_clef: MagicMock,
    ) -> None:
        mock_clef = MagicMock()
        mock_clef.triage.return_value = _make_dummy_clef_decision()
        mock_clef.vram_allocated_bytes.return_value = 3_500_000_000
        mock_get_clef.return_value = mock_clef

        mock_gemini = MagicMock()
        mock_gemini.model_name = "gemini-2.5-flash"
        mock_gemini.triage.return_value = _make_dummy_gemini_result()
        mock_get_gemini.return_value = mock_gemini

        payload = {"incident_text": SAMPLE_CLAIM_TEXT}
        response = client.post("/api/triage/compare", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Validate against Pydantic schema
        validated = TriageComparisonResponse.model_validate(data)
        assert validated.incident_text == SAMPLE_CLAIM_TEXT
        assert validated.clef_result.success is True
        assert validated.gemini_result.success is True
        assert validated.clef_result.jira_tickets is not None
        assert validated.gemini_result.jira_tickets is not None
        assert validated.discrepancy_detected is False
        assert validated.cost_delta_projected_100k_usd > 0

    def test_compare_endpoint_validation_error_on_short_text(self) -> None:
        payload = {"incident_text": "Choque leve"}  # < 15 characters
        response = client.post("/api/triage/compare", json=payload)
        assert response.status_code == 422

    @patch("app.main.get_clef_service")
    @patch("app.main.get_gemini_service")
    def test_compare_endpoint_detects_discrepancy(
        self,
        mock_get_gemini: MagicMock,
        mock_get_clef: MagicMock,
    ) -> None:
        # Clef says Generales P2
        mock_clef = MagicMock()
        mock_clef.triage.return_value = _make_dummy_clef_decision()
        mock_clef.vram_allocated_bytes.return_value = 0
        mock_get_clef.return_value = mock_clef

        # Gemini says Vida y Personas P1
        gemini_decision = TriageDecision(
            macro_ramo=MacroRamo.VIDA_Y_PERSONAS,
            ramo_especifico=RamoEspecifico.ACCIDENTES_PERSONALES,
            severidad=1,
            involucra_terceros=False,
            indicio_lesiones_corporales=True,
        )
        gemini_metrics = ModelExecutionMetrics(latency_ms=600.0)
        mock_gemini = MagicMock()
        mock_gemini.model_name = "gemini-2.5-flash"
        mock_gemini.triage.return_value = GeminiTriageResult(
            decision=gemini_decision,
            metrics=gemini_metrics,
        )
        mock_get_gemini.return_value = mock_gemini

        response = client.post("/api/triage/compare", json={"incident_text": SAMPLE_CLAIM_TEXT})
        assert response.status_code == 200
        data = response.json()
        assert data["discrepancy_detected"] is True

    @patch("app.main.get_clef_service")
    @patch("app.main.get_gemini_service")
    def test_compare_endpoint_graceful_model_failure(
        self,
        mock_get_gemini: MagicMock,
        mock_get_clef: MagicMock,
    ) -> None:
        mock_clef = MagicMock()
        mock_clef.triage.side_effect = RuntimeError("CUDA OOM simulated")
        mock_get_clef.return_value = mock_clef

        mock_gemini = MagicMock()
        mock_gemini.model_name = "gemini-2.5-flash"
        mock_gemini.triage.return_value = _make_dummy_gemini_result()
        mock_get_gemini.return_value = mock_gemini

        response = client.post("/api/triage/compare", json={"incident_text": SAMPLE_CLAIM_TEXT})
        assert response.status_code == 200
        data = response.json()
        assert data["clef_result"]["success"] is False
        assert "CUDA OOM" in data["clef_result"]["error_message"]
        assert data["gemini_result"]["success"] is True
