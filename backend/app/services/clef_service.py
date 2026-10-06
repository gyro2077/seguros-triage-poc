"""Local System 1 inference service for Cloudflare/clef-flash (4-bit, single forward pass).

Clef-Flash does not generate text: it scores every allowed option of every typed question
in one forward pass. We map those scores directly onto the enums of ``app.schemas``.
"""

from __future__ import annotations

import importlib.util
import sys
import threading
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Optional

import torch

from app.schemas import (
    RAMOS_GENERALES,
    RAMOS_VIDA_PERSONAS,
    MacroRamo,
    RamoEspecifico,
    TriageDecision,
)

MODEL_ID: str = "Cloudflare/clef-flash"
VRAM_LIMIT_BYTES: int = int(6.2 * 1024**3)
SEVERITY_LEVELS: int = 4
BOOL_THRESHOLD: float = 0.5
# Below this top-probability on branch / macro-ramo, flag the claim for expert review.
LOW_CONFIDENCE_THRESHOLD: float = 0.5

STATE_QUESTIONS: dict[str, dict[str, Any]] = {
    "macro_ramo": {
        "type": "choice",
        "instructions": "Which insurance macro-branch does this claim belong to?",
        "criteria": {
            MacroRamo.GENERALES.value: "Property, vehicle, liability, cargo, machinery or bond claims.",
            MacroRamo.VIDA_Y_PERSONAS.value: "Health, accident, life or funeral claims about people.",
            MacroRamo.MIXTO.value: "Claim spanning both property/general and people/life coverages.",
        },
    },
    "ramo_especifico": {
        "type": "choice",
        "instructions": "Which specific insurance branch is the main subject of the claim?",
        "criteria": {
            RamoEspecifico.VEHICULOS.value: "Vehicle collision, theft or damage.",
            RamoEspecifico.TODO_RIESGO_CONTRATISTA_MONTAJE.value: "Construction or assembly all-risk damage.",
            RamoEspecifico.INCENDIO_LINEAS_ALIADAS.value: "Fire, explosion, flood or allied perils on property.",
            RamoEspecifico.TRANSPORTE_CARGA.value: "Damage or loss of transported cargo.",
            RamoEspecifico.RESPONSABILIDAD_CIVIL.value: "Liability for damage caused to third parties.",
            RamoEspecifico.FIANZAS_GARANTIAS.value: "Surety bonds and guarantees.",
            RamoEspecifico.ROTURA_MAQUINARIA.value: "Breakdown of industrial machinery or equipment.",
            RamoEspecifico.ASISTENCIA_MEDICA_SALUD.value: "Medical assistance and health expenses.",
            RamoEspecifico.ACCIDENTES_PERSONALES.value: "Personal accident injuries or disability.",
            RamoEspecifico.VIDA_INDIVIDUAL_O_COLECTIVO.value: "Death of an insured under life policy.",
            RamoEspecifico.EXEQUIAS_SEPELIO.value: "Funeral and burial expenses.",
        },
    },
    "involucra_terceros": {
        "type": "noul",
        "instructions": "Does the incident involve third parties other than the policyholder?",
    },
    "indicio_lesiones_corporales": {
        "type": "noul",
        "instructions": "Is there any indication of bodily injuries to any person?",
    },
    "severidad": {
        "type": "score",
        "instructions": "Rate the actuarial severity of the claim.",
        "criteria": [
            "P1 Critico: deaths, severe injuries or total loss, attend in under 2 hours.",
            "P2 Alto: significant damage or injuries, attend in under 6 hours.",
            "P3 Medio: moderate damage without injuries, attend in under 24 hours.",
            "P4 Bajo: minor damage, attend in under 48 hours.",
        ],
    },
    "requiere_revision_pericial": {
        "type": "noul",
        "instructions": "Is the incident ambiguous or does it require manual expert assessment?",
    },
}


class _CpuLookup:
    """Indexable proxy: gathers rows of a CPU tensor with CUDA ids, returns CUDA bf16 rows."""

    def __init__(self, weight: torch.Tensor) -> None:
        self._weight = weight

    def __getitem__(self, ids: torch.Tensor) -> torch.Tensor:
        return self._weight[ids.cpu()].to(device="cuda", dtype=torch.bfloat16)


class ClefServiceError(RuntimeError):
    """Raised when the local Clef-Flash model cannot be loaded or evaluated."""


def _load_release_module(model_path: Path) -> ModuleType:
    """Import ``joint_schema_model.py`` shipped with the model snapshot."""
    spec = importlib.util.spec_from_file_location(
        "joint_schema_model", model_path / "joint_schema_model.py"
    )
    if spec is None or spec.loader is None:
        raise ClefServiceError(f"joint_schema_model.py not found in {model_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["joint_schema_model"] = module
    spec.loader.exec_module(module)
    return module


class ClefService:
    """Loads Clef-Flash in 4-bit on CUDA and evaluates TriageDecision via direct option scoring."""

    def __init__(self, model_id: str = MODEL_ID) -> None:
        self._model_id: str = model_id
        self._model: Optional[Any] = None
        self._processor: Optional[Any] = None
        self._module: Optional[ModuleType] = None
        self._lexical_weight: Optional[torch.Tensor] = None
        self._lock: threading.Lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        """Load backbone (NF4 4-bit) + joint head. Idempotent."""
        if self._model is not None:
            return
        if not torch.cuda.is_available():
            raise ClefServiceError("CUDA is required for Clef-Flash local inference")
        from huggingface_hub import snapshot_download
        from safetensors import safe_open
        from safetensors.torch import load_file
        from transformers import (
            AutoTokenizer,
            BitsAndBytesConfig,
            Qwen3_5ForConditionalGeneration,
        )

        path = Path(snapshot_download(self._model_id))
        module = _load_release_module(path)
        quant = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            llm_int8_skip_modules=["visual", "lm_head"],
            llm_int8_enable_fp32_cpu_offload=True,
        )
        # Text-only triage: the vision tower is never used, keep it off the GPU.
        backbone = Qwen3_5ForConditionalGeneration.from_pretrained(
            path,
            dtype=torch.bfloat16,
            quantization_config=quant,
            device_map={
                "model.visual": "cpu",
                "model.language_model.embed_tokens": "cpu",
                "model.language_model.layers": 0,
                "model.language_model.norm": 0,
                "model.language_model.rotary_emb": 0,
                "lm_head": "cpu",
            },
        )
        backbone.config.use_cache = False
        import json

        head_cfg = json.loads((path / "joint_head_config.json").read_text())
        head = module.JointSchemaHead(**head_cfg)
        head.load_state_dict(load_file(path / "joint_head.safetensors"), strict=True)
        head = head.to(device="cuda", dtype=torch.bfloat16)
        self._model = module.ClefModel(backbone, head).eval()
        index = json.loads((path / "model.safetensors.index.json").read_text())
        shard = index["weight_map"]["lm_head.weight"]
        with safe_open(path / shard, framework="pt", device="cpu") as f:
            self._lexical_weight = f.get_tensor("lm_head.weight")
        self._processor = AutoTokenizer.from_pretrained(path)
        self._module = module

    def vram_allocated_bytes(self) -> int:
        return int(torch.cuda.memory_allocated())

    def _forward(self, batch: dict[str, Any]) -> list[list[torch.Tensor]]:
        """Text-only forward; lexical lookups on the CPU-resident lm_head weight."""
        assert self._model is not None and self._lexical_weight is not None
        model = self._model
        text_model = model.language_model.model.language_model
        outputs = text_model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            use_cache=False,
            return_dict=True,
        )
        weight = _CpuLookup(self._lexical_weight)
        return model.head(
            outputs.last_hidden_state,
            batch["input_ids"],
            batch["attention_mask"],
            batch["records"],
            weight,
        )

    def _scores(self, incident_text: str) -> dict[str, dict[str, float]]:
        """One forward pass -> softmax probabilities per question option."""
        assert self._model is not None and self._processor is not None and self._module is not None
        tokenizer = self._processor
        record: dict[str, Any] = {"state": incident_text, "questions": STATE_QUESTIONS}
        encoded = self._module.encode_record(tokenizer, record)
        device = torch.device("cuda")
        batch = self._module.collate_records([encoded], tokenizer.pad_token_id, device)
        with self._lock, torch.inference_mode():
            logits = self._forward(batch)[0]
        return {
            q.question_id: dict(zip(q.option_ids, lg.float().softmax(-1).tolist()))
            for q, lg in zip(encoded.questions, logits)
        }

    def triage(self, incident_text: str) -> TriageDecision:
        """Classify a claim narrative into a validated TriageDecision."""
        self.load()
        probs = self._scores(incident_text)
        return self._to_decision(probs)

    @staticmethod
    def _to_decision(probs: dict[str, dict[str, float]]) -> TriageDecision:
        macro_p = probs["macro_ramo"]
        macro = MacroRamo(max(macro_p, key=lambda k: macro_p[k]))
        ramo_p = {RamoEspecifico(k): v for k, v in probs["ramo_especifico"].items()}

        def best(allowed: set[RamoEspecifico]) -> RamoEspecifico:
            return max(allowed, key=lambda r: ramo_p[r])

        secondary: Optional[RamoEspecifico] = None
        if macro == MacroRamo.GENERALES:
            primary = best(RAMOS_GENERALES)
        elif macro == MacroRamo.VIDA_Y_PERSONAS:
            primary = best(RAMOS_VIDA_PERSONAS)
        else:
            primary = max(ramo_p, key=lambda r: ramo_p[r])
            opposite = RAMOS_VIDA_PERSONAS if primary in RAMOS_GENERALES else RAMOS_GENERALES
            secondary = best(opposite)

        sev_p = probs["severidad"]
        severity = int(max(sev_p, key=lambda k: sev_p[k])) + 1
        low_conf = (
            max(macro_p.values()) < LOW_CONFIDENCE_THRESHOLD
            or ramo_p[primary] < LOW_CONFIDENCE_THRESHOLD
        )
        return TriageDecision(
            macro_ramo=macro,
            ramo_especifico=primary,
            involucra_terceros=probs["involucra_terceros"]["true"] > BOOL_THRESHOLD,
            indicio_lesiones_corporales=probs["indicio_lesiones_corporales"]["true"] > BOOL_THRESHOLD,
            severidad=min(max(severity, 1), SEVERITY_LEVELS),
            requiere_revision_pericial=probs["requiere_revision_pericial"]["true"] > BOOL_THRESHOLD
            or low_conf,
            ramo_secundario=secondary,
        )


_service: Optional[ClefService] = None


def get_clef_service() -> ClefService:
    """Process-wide singleton accessor."""
    global _service
    if _service is None:
        _service = ClefService()
    return _service
