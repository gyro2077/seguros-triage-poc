"""Unit and integration tests for Gemini 2.5 Flash service (T3).

Includes comprehensive mocked tests for structured JSON outputs, telemetry,
cost calculations, and error handling, plus a conditional live integration test.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from app.schemas import (
    MacroRamo,
    ModelExecutionMetrics,
    ModelTriageResult,
    RamoEspecifico,
    TriageDecision,
)
from app.services.gemini_service import (
    DEFAULT_MODEL_ID,
    GEMINI_INPUT_COST_PER_MILLION,
    GEMINI_OUTPUT_COST_PER_MILLION,
    GeminiService,
    GeminiServiceError,
    GeminiTriageResult,
)

SAMPLE_CLAIM_TEXT = (
    "Choque por alcance en la Av. Simón Bolívar, Quito. El vehículo asegurado impactó contra "
    "un taxi de un tercero. No se reportan personas heridas ni fallecidas, únicamente daños "
    "materiales de consideración en el guardafango y faros delanteros."
)

VALID_DECISION_JSON = """{
    "macro_ramo": "GENERALES",
    "ramo_especifico": "VEHICULOS",
    "involucra_terceros": true,
    "indicio_lesiones_corporales": false,
    "severidad": 2,
    "requiere_revision_pericial": false,
    "ramo_secundario": null
}"""


def _create_mock_response(
    json_text: str = VALID_DECISION_JSON,
    prompt_tokens: int = 150,
    candidates_tokens: int = 60,
) -> MagicMock:
    """Helper creating a mock response matching google-genai response structure."""
    mock_response = MagicMock()
    mock_response.text = json_text
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.prompt_token_count = prompt_tokens
    mock_response.usage_metadata.candidates_token_count = candidates_tokens
    return mock_response


class TestGeminiAuthentication:
    """Authentication and initialization constraints."""

    def test_missing_api_key_raises_runtime_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When GEMINI_API_KEY is not set and no key passed, must raise RuntimeError."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY no configurada"):
            GeminiService()

    def test_explicit_api_key_initializes_service(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Explicit key passed to constructor overrides environment and succeeds."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        service = GeminiService(api_key="explicit_test_key")
        assert service.model_name == DEFAULT_MODEL_ID


class TestGeminiStructuredOutputsAndTelemetry:
    """Validates structured JSON output parsing, token extraction, and cost formulas."""

    def test_gemini_triage_success_and_field_mapping(self) -> None:
        """Verify mock response maps strictly to TriageDecision with telemetry."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = _create_mock_response(
            json_text=VALID_DECISION_JSON,
            prompt_tokens=200,
            candidates_tokens=50,
        )

        service = GeminiService(api_key="test_key", client=mock_client)
        result = service.triage(SAMPLE_CLAIM_TEXT)

        assert isinstance(result, GeminiTriageResult)
        assert isinstance(result.decision, TriageDecision)
        assert result.decision.macro_ramo == MacroRamo.GENERALES
        assert result.decision.ramo_especifico == RamoEspecifico.VEHICULOS
        assert result.decision.involucra_terceros is True
        assert result.decision.indicio_lesiones_corporales is False
        assert result.decision.severidad == 2
        assert result.decision.requiere_revision_pericial is False

        metrics = result.metrics
        assert isinstance(metrics, ModelExecutionMetrics)
        assert metrics.prompt_tokens == 200
        assert metrics.completion_tokens == 50
        assert metrics.total_tokens == 250
        assert metrics.latency_ms >= 0.0
        assert metrics.vram_allocated_mb is None

        # Verify cost formulas
        expected_cost = (200 / 1_000_000.0) * GEMINI_INPUT_COST_PER_MILLION + (
            50 / 1_000_000.0
        ) * GEMINI_OUTPUT_COST_PER_MILLION
        assert metrics.estimated_cost_usd == pytest.approx(expected_cost, abs=1e-6)
        assert metrics.projected_cost_100k_usd == pytest.approx(expected_cost * 100_000, abs=1e-4)

    def test_gemini_triage_tuple_unpacking(self) -> None:
        """Ensure GeminiTriageResult cleanly unpacks as (decision, metrics)."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = _create_mock_response()

        service = GeminiService(api_key="test_key", client=mock_client)
        decision, metrics = service.triage(SAMPLE_CLAIM_TEXT)

        assert isinstance(decision, TriageDecision)
        assert isinstance(metrics, ModelExecutionMetrics)

    def test_gemini_config_enforces_pydantic_schema_and_json_mime(self) -> None:
        """Call to Gemini must enforce response_mime_type and response_schema."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = _create_mock_response()

        service = GeminiService(api_key="test_key", client=mock_client)
        service.triage(SAMPLE_CLAIM_TEXT)

        mock_client.models.generate_content.assert_called_once()
        _, kwargs = mock_client.models.generate_content.call_args
        config = kwargs.get("config")
        assert config is not None
        assert config.response_mime_type == "application/json"
        assert config.response_schema == TriageDecision
        assert config.temperature == 0.0

    def test_gemini_triage_full_returns_model_triage_result(self) -> None:
        """triage_full helper returns a complete ModelTriageResult."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = _create_mock_response()

        service = GeminiService(api_key="test_key", client=mock_client)
        full_result = service.triage_full(SAMPLE_CLAIM_TEXT)

        assert isinstance(full_result, ModelTriageResult)
        assert full_result.model_name == "gemini-2.5-flash"
        assert full_result.success is True
        assert full_result.schema_valid is True
        assert full_result.decision is not None
        assert full_result.metrics.prompt_tokens == 150

    def test_gemini_cost_calculation_known_values(self) -> None:
        """Check exact pricing math against known token volumes."""
        mock_client = MagicMock()
        # 1M prompt tokens and 1M completion tokens
        mock_client.models.generate_content.return_value = _create_mock_response(
            prompt_tokens=1_000_000,
            candidates_tokens=1_000_000,
        )

        service = GeminiService(api_key="test_key", client=mock_client)
        result = service.triage(SAMPLE_CLAIM_TEXT)

        # $0.075 + $0.30 = $0.375
        assert result.metrics.estimated_cost_usd == pytest.approx(0.375, abs=1e-5)
        # 100k requests would be $37,500.0
        assert result.metrics.projected_cost_100k_usd == pytest.approx(37500.0, abs=1e-2)


class TestGeminiErrorHandling:
    """Robust handling of API failures, empty responses, and invalid schemas."""

    def test_api_network_error_raises_service_error(self) -> None:
        """Connection or upstream errors raise GeminiServiceError."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("Network timeout")

        service = GeminiService(api_key="test_key", client=mock_client)
        with pytest.raises(GeminiServiceError, match="Error calling Gemini API"):
            service.triage(SAMPLE_CLAIM_TEXT)

    def test_empty_response_raises_service_error(self) -> None:
        """Empty response string raises GeminiServiceError."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = _create_mock_response(json_text="")

        service = GeminiService(api_key="test_key", client=mock_client)
        with pytest.raises(GeminiServiceError, match="empty response body"):
            service.triage(SAMPLE_CLAIM_TEXT)

    def test_inconsistent_actuarial_schema_raises_service_error(self) -> None:
        """Invalid actuarial combination (e.g. GENERALES with ASISTENCIA_MEDICA_SALUD) raises GeminiServiceError."""
        invalid_actuarial_json = """{
            "macro_ramo": "GENERALES",
            "ramo_especifico": "ASISTENCIA_MEDICA_SALUD",
            "involucra_terceros": false,
            "indicio_lesiones_corporales": false,
            "severidad": 3,
            "requiere_revision_pericial": false,
            "ramo_secundario": null
        }"""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = _create_mock_response(
            json_text=invalid_actuarial_json
        )

        service = GeminiService(api_key="test_key", client=mock_client)
        with pytest.raises(GeminiServiceError, match="Failed to validate Gemini response"):
            service.triage(SAMPLE_CLAIM_TEXT)


@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY no presente en el entorno; omitiendo test de integración real.",
)
def test_gemini_live_integration() -> None:
    """Real live API integration test executed only when GEMINI_API_KEY is configured."""
    service = GeminiService()
    result = service.triage(SAMPLE_CLAIM_TEXT)

    assert isinstance(result.decision, TriageDecision)
    assert result.decision.macro_ramo in (MacroRamo.GENERALES, MacroRamo.MIXTO)
    assert result.metrics.prompt_tokens > 0
    assert result.metrics.completion_tokens > 0
    assert result.metrics.latency_ms > 0
    assert result.metrics.estimated_cost_usd > 0
