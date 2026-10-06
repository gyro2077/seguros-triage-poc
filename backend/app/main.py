"""FastAPI application for Insurance Claims Triage Benchmark (T4).

Compares System 1 local model (Clef-Flash) against System 2 cloud model (Gemini 2.5 Flash)
in parallel, generating Jira Service Management tickets and telemetry metrics.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict

import torch
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    ModelExecutionMetrics,
    ModelTriageResult,
    TriageComparisonResponse,
    TriageRequest,
)
from app.services.clef_service import get_clef_service
from app.services.gemini_service import get_gemini_service
from app.services.jira_mapper import map_decision_to_jira

app = FastAPI(
    title="Motor de Triage de Siniestros (Clef vs Gemini)",
    description="Plataforma de comparación actuarial en tiempo real entre Clef-Flash local y Gemini 2.5 Flash Cloud.",
    version="1.0.0",
)

# CORS configuration for React/Vite frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _execute_clef(incident_text: str) -> ModelTriageResult:
    """Synchronous worker execution for Clef-Flash on PyTorch CUDA."""
    service = get_clef_service()
    start = time.perf_counter()
    try:
        decision = service.triage(incident_text)
        latency_ms = (time.perf_counter() - start) * 1000.0
        vram_mb = service.vram_allocated_bytes() / (1024**2) if torch.cuda.is_available() else None
        jira_tickets = map_decision_to_jira(decision, incident_text=incident_text)

        metrics = ModelExecutionMetrics(
            latency_ms=round(latency_ms, 2),
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost_usd=0.0,
            projected_cost_100k_usd=0.0,
            vram_allocated_mb=round(vram_mb, 2) if vram_mb is not None else None,
        )
        return ModelTriageResult(
            model_name="clef-flash",
            success=True,
            schema_valid=True,
            decision=decision,
            jira_tickets=jira_tickets,
            metrics=metrics,
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return ModelTriageResult(
            model_name="clef-flash",
            success=False,
            schema_valid=False,
            metrics=ModelExecutionMetrics(latency_ms=round(latency_ms, 2)),
            error_message=str(exc),
        )


def _execute_gemini(incident_text: str) -> ModelTriageResult:
    """Synchronous worker execution for Gemini cloud call."""
    service = get_gemini_service()
    start = time.perf_counter()
    try:
        res = service.triage(incident_text)
        jira_tickets = map_decision_to_jira(res.decision, incident_text=incident_text)
        return ModelTriageResult(
            model_name=service.model_name,
            success=True,
            schema_valid=True,
            decision=res.decision,
            jira_tickets=jira_tickets,
            metrics=res.metrics,
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return ModelTriageResult(
            model_name=service.model_name,
            success=False,
            schema_valid=False,
            metrics=ModelExecutionMetrics(latency_ms=round(latency_ms, 2)),
            error_message=str(exc),
        )


@app.get("/api/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint reporting GPU status and model readiness."""
    gpu_available = bool(torch.cuda.is_available())
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else None
    clef_service = get_clef_service()
    gemini_service = get_gemini_service()

    return {
        "status": "ok",
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "clef_loaded": clef_service.is_loaded,
        "gemini_model": gemini_service.model_name,
    }


@app.post("/api/triage/compare", response_model=TriageComparisonResponse, status_code=status.HTTP_200_OK)
async def compare_triage(request: TriageRequest) -> TriageComparisonResponse:
    """Parallel comparison endpoint executing Clef and Gemini concurrently."""
    # Execute both inference workloads asynchronously in threadpool to keep the event loop non-blocking
    clef_task = asyncio.to_thread(_execute_clef, request.incident_text)
    gemini_task = asyncio.to_thread(_execute_gemini, request.incident_text)

    clef_result, gemini_result = await asyncio.gather(clef_task, gemini_task)

    discrepancy = False
    if clef_result.decision and gemini_result.decision:
        discrepancy = (
            clef_result.decision.macro_ramo != gemini_result.decision.macro_ramo
            or clef_result.decision.severidad != gemini_result.decision.severidad
        )

    cost_delta = (
        gemini_result.metrics.projected_cost_100k_usd
        - clef_result.metrics.projected_cost_100k_usd
    )

    return TriageComparisonResponse(
        incident_id=str(uuid.uuid4()),
        incident_text=request.incident_text,
        clef_result=clef_result,
        gemini_result=gemini_result,
        discrepancy_detected=discrepancy,
        cost_delta_projected_100k_usd=round(cost_delta, 2),
    )
