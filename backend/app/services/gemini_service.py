"""Cloud System 2 inference service using Google GenAI SDK (Gemini 2.5 Flash).

Uses strict JSON structured outputs with the ``TriageDecision`` Pydantic schema,
extracts full token telemetry from ``usage_metadata``, and calculates exact USD cost.
"""

from __future__ import annotations

import os
import time
from typing import NamedTuple, Optional

from google import genai
from google.genai import types

from app.schemas import (
    ModelExecutionMetrics,
    ModelTriageResult,
    TriageDecision,
)

DEFAULT_MODEL_ID: str = "gemini-2.5-flash"

# Pricing per million tokens (Gemini 2.5 Flash / 2.0 Flash standard rates)
GEMINI_INPUT_COST_PER_MILLION: float = 0.075
GEMINI_OUTPUT_COST_PER_MILLION: float = 0.30

SYSTEM_INSTRUCTION: str = (
    "Eres un actuario y perito experto en seguros según la regulación ecuatoriana "
    "(Superintendencia de Compañías, Valores y Seguros). Tu función es clasificar de manera "
    "estricta y objetiva los relatos de siniestros en el esquema de triage estructurado proporcionado.\n\n"
    "Reglas actuariales:\n"
    "1. MacroRamo GENERALES incluye: VEHICULOS, TODO_RIESGO_CONTRATISTA_MONTAJE, INCENDIO_LINEAS_ALIADAS, "
    "TRANSPORTE_CARGA, RESPONSABILIDAD_CIVIL, FIANZAS_GARANTIAS, ROTURA_MAQUINARIA.\n"
    "2. MacroRamo VIDA_Y_PERSONAS incluye: ASISTENCIA_MEDICA_SALUD, ACCIDENTES_PERSONALES, "
    "VIDA_INDIVIDUAL_O_COLECTIVO, EXEQUIAS_SEPELIO.\n"
    "3. MacroRamo MIXTO: cuando el siniestro afecta tanto bienes/responsabilidad (Generales) como "
    "personas/salud/vida (Vida y Personas). En este caso, ramo_secundario DEBE pertenecer a la categoría opuesta "
    "al ramo_especifico principal.\n"
    "4. Severidad (1 a 4):\n"
    "   - 1 (P1 - Crítico): Fallecimiento, lesiones corporales graves que amenazan la vida o pérdida total catastrófica (SLA < 2h).\n"
    "   - 2 (P2 - Alto): Daños estructurales/materiales severos o lesiones que requieren hospitalización (SLA < 6h).\n"
    "   - 3 (P3 - Medio): Daños materiales moderados sin lesiones corporales (SLA < 24h).\n"
    "   - 4 (P4 - Bajo): Daños leves o reclamos menores/documentarios (SLA < 48h).\n"
    "5. Requiere revisión pericial: true si el relato es ambiguo, sospechoso o de alta complejidad pericial.\n"
    "Debes devolver exclusivamente la estructura JSON correspondiente a TriageDecision."
)


class GeminiServiceError(RuntimeError):
    """Raised when the Gemini API cannot be reached or returns an unparsable response."""


class GeminiTriageResult(NamedTuple):
    """Tuple containing the actuarial decision and telemetry metrics."""

    decision: TriageDecision
    metrics: ModelExecutionMetrics


class GeminiService:
    """Evaluates TriageDecision via Google GenAI SDK with structured schema enforcement."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        client: Optional[genai.Client] = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self._api_key and client is None:
            raise RuntimeError("GEMINI_API_KEY no configurada")

        self._model_name = (
            model_name
            or os.environ.get("GEMINI_MODEL")
            or DEFAULT_MODEL_ID
        )
        self._client = client or genai.Client(api_key=self._api_key)

    @property
    def model_name(self) -> str:
        return self._model_name

    def triage(self, incident_text: str) -> GeminiTriageResult:
        """Classify a claim incident narrative using structured JSON outputs."""
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=TriageDecision,
            temperature=0.0,
        )

        start_time = time.perf_counter()
        response = None
        last_exc: Optional[Exception] = None
        for attempt in range(3):
            try:
                response = self._client.models.generate_content(
                    model=self._model_name,
                    contents=incident_text,
                    config=config,
                )
                break
            except Exception as exc:
                last_exc = exc
                if attempt < 2 and ("503" in str(exc) or "429" in str(exc) or "UNAVAILABLE" in str(exc)):
                    time.sleep(1.0 * (attempt + 1))
                    continue
                raise GeminiServiceError(
                    f"Error calling Gemini API ({self._model_name}): {exc}"
                ) from exc

        if response is None:
            raise GeminiServiceError(
                f"Error calling Gemini API ({self._model_name}): {last_exc}"
            )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        raw_text = response.text
        if not raw_text:
            raise GeminiServiceError("Gemini API returned an empty response body.")

        try:
            decision = TriageDecision.model_validate_json(raw_text)
        except Exception as exc:
            raise GeminiServiceError(
                f"Failed to validate Gemini response against TriageDecision: {exc}"
            ) from exc

        prompt_tokens = 0
        completion_tokens = 0
        if response.usage_metadata is not None:
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

        total_tokens = prompt_tokens + completion_tokens
        cost_usd = (prompt_tokens / 1_000_000.0) * GEMINI_INPUT_COST_PER_MILLION + (
            completion_tokens / 1_000_000.0
        ) * GEMINI_OUTPUT_COST_PER_MILLION
        projected_100k = cost_usd * 100_000.0

        metrics = ModelExecutionMetrics(
            latency_ms=round(latency_ms, 2),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=round(cost_usd, 6),
            projected_cost_100k_usd=round(projected_100k, 4),
            vram_allocated_mb=None,
        )

        return GeminiTriageResult(decision=decision, metrics=metrics)

    def triage_full(self, incident_text: str) -> ModelTriageResult:
        """Helper returning the full ModelTriageResult schema."""
        result = self.triage(incident_text)
        return ModelTriageResult(
            model_name=self._model_name,
            success=True,
            schema_valid=True,
            decision=result.decision,
            metrics=result.metrics,
        )


_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Process-wide singleton accessor."""
    global _service
    if _service is None:
        _service = GeminiService()
    return _service
