"""Authentication and immutable projection of the Stage 7 authority."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping
from TradingSystemLab.authority_hashing import canonical_authority_sha256

PRODUCTION_SPECIFICATION_ID = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
ACTIVE_IDENTITY = "TRAIL1__N4_01__FULL__R15"
INSTRUMENTS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
STAGE7 = Path(__file__).resolve().parents[1] / "results/post_v3_analysis/stage7_production_specification_freeze"

class SpecificationError(RuntimeError): pass

@dataclass(frozen=True)
class FrozenSpecification:
    production_id: str
    identity: str
    strategy: Mapping[str, Any]
    variant: Mapping[str, Any]
    instruments: tuple[str, ...]
    risk_fraction: float
    maximum_nominal_risk: float

def load_frozen_specification(stage7: Path = STAGE7) -> FrozenSpecification:
    """Validate the ID, canonical payload, audit, and every provenance hash."""
    required = ("production_specification.json", "strategy_identity.json", "source_provenance.json",
                "independent_audit_result.json", "PRODUCTION_SPECIFICATION.md", "risk_and_sizing_contract.md",
                "execution_semantics.md", "state_persistence_contract.md", "data_contract.md",
                "research_to_robot_conformance.md", "instrument_registry.csv")
    missing = [name for name in required if not (stage7 / name).is_file()]
    if missing: raise SpecificationError(f"STAGE7_MISSING:{','.join(missing)}")
    spec = json.loads((stage7 / "production_specification.json").read_text(encoding="utf-8"))
    audit = json.loads((stage7 / "independent_audit_result.json").read_text(encoding="utf-8"))
    if audit.get("status") != "PASS": raise SpecificationError("STAGE7_AUDIT_NOT_PASS")
    payload = dict(spec); sid = payload.pop("production_specification_id", None); recorded = payload.pop("canonical_active_payload_sha256", None)
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if sid != PRODUCTION_SPECIFICATION_ID or recorded != digest or sid != "PROD_STAGE7_" + digest.upper():
        raise SpecificationError("STAGE7_SPECIFICATION_ID_OR_HASH_MISMATCH")
    if spec.get("identity") != ACTIVE_IDENTITY: raise SpecificationError("STAGE7_ACTIVE_IDENTITY_MISMATCH")
    provenance = json.loads((stage7 / "source_provenance.json").read_text(encoding="utf-8"))
    root = stage7.parents[3]
    for item in provenance.values():
        if "path" not in item: continue
        source = root / item["path"]
        if not source.is_file() or canonical_authority_sha256(source) != item["sha256"]: raise SpecificationError(f"STAGE7_SOURCE_HASH_MISMATCH:{item['path']}")
    expected = {"name":"T3", "candidate":"T3_H1_candidate_v3", "timeframe":"H1"}
    if any(spec["strategy"].get(k) != v for k,v in expected.items()) or spec["variant"].get("name") != "TRAIL1":
        raise SpecificationError("FROZEN_STRATEGY_MISMATCH")
    if tuple(spec["basket"]["instruments"]) != INSTRUMENTS or spec["risk"]["mode"] != "R15" or spec["risk"]["load"] != "FULL":
        raise SpecificationError("FROZEN_PORTFOLIO_MISMATCH")
    return FrozenSpecification(sid, spec["identity"], MappingProxyType(spec["strategy"]), MappingProxyType(spec["variant"]),
                               INSTRUMENTS, spec["risk"]["risk_fraction_per_new_instrument_position"],
                               spec["risk"]["maximum_nominal_simultaneous_initial_risk"])
