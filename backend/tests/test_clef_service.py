"""Tests for the local Clef-Flash service (requires CUDA GPU and downloaded model)."""

import statistics
import time

import pytest
import torch

from app.schemas import MacroRamo, RamoEspecifico, TriageDecision
from app.services.clef_service import VRAM_LIMIT_BYTES, ClefService

CLAIM = (
    "El asegurado chocó su vehículo contra otro auto en la Av. Amazonas; el conductor "
    "del otro vehículo sufrió fracturas y fue trasladado al hospital."
)

pytestmark = pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required")


@pytest.fixture(scope="module")
def service() -> ClefService:
    svc = ClefService()
    t0 = time.perf_counter()
    svc.load()
    svc.triage(CLAIM)  # warm-up
    torch.cuda.synchronize()
    print(f"\nLOAD+WARMUP_S={time.perf_counter() - t0:.2f}")
    return svc


def test_returns_valid_triage_decision(service: ClefService) -> None:
    decision = service.triage(CLAIM)
    assert isinstance(decision, TriageDecision)
    assert isinstance(decision.macro_ramo, MacroRamo)
    assert isinstance(decision.ramo_especifico, RamoEspecifico)
    assert isinstance(decision.involucra_terceros, bool)
    assert isinstance(decision.indicio_lesiones_corporales, bool)
    assert isinstance(decision.severidad, int) and 1 <= decision.severidad <= 4
    assert decision.ramo_especifico in {
        RamoEspecifico.VEHICULOS,
        RamoEspecifico.RESPONSABILIDAD_CIVIL,
    }
    assert decision.involucra_terceros is True
    assert decision.indicio_lesiones_corporales is True


def test_latency_under_threshold_after_warmup(service: ClefService) -> None:
    times: list[float] = []
    for _ in range(5):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        service.triage(CLAIM)
        torch.cuda.synchronize()
        times.append((time.perf_counter() - t0) * 1000)
    median = statistics.median(times)
    print(f"\nLATENCY_MS median={median:.1f} max={max(times):.1f}")
    # On RTX 4060 Laptop (8GB VRAM) with 4-bit quantization, full forward pass is ~1.1s.
    assert median < 1500, f"median latency {median:.1f} ms"


def test_vram_within_limit(service: ClefService) -> None:
    service.triage(CLAIM)
    allocated = torch.cuda.memory_allocated()
    peak = torch.cuda.max_memory_allocated()
    print(f"\nVRAM_ALLOCATED_GB={allocated / 1024**3:.3f} PEAK_GB={peak / 1024**3:.3f}")
    assert allocated == service.vram_allocated_bytes()
    assert allocated <= VRAM_LIMIT_BYTES
