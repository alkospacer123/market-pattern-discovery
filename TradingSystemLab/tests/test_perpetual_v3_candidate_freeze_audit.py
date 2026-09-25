import copy
import hashlib
import json
from pathlib import Path

import pytest

from TradingSystemLab.audit_perpetual_v3_candidate_freeze import audit
from TradingSystemLab.perpetual_v3_candidate_freeze import generate

ROOT = Path(__file__).resolve().parents[2]


def _write_bundle(output, registry, manifest):
    registry_path = output / "candidate_registry.json"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n")
    # Bind registry mutations so the substantive independent check is exercised.
    manifest["artifact_sha256"]["candidate_registry.json"] = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def mutations(registry, manifest):
    cases = []
    def reg(label, edit):
        r, m = copy.deepcopy(registry), copy.deepcopy(manifest); edit(r); cases.append((label, r, m))
    def man(label, edit):
        r, m = copy.deepcopy(registry), copy.deepcopy(manifest); edit(m); cases.append((label, r, m))
    reg("configuration", lambda r: r["candidates"][0].update(phase2_configuration_id="bad"))
    reg("parameters", lambda r: r["candidates"][0]["parameters"].update(max_initial_stop_atr=2.4))
    reg("parameter hash", lambda r: r["candidates"][0].update(parameter_hash="0" * 64))
    reg("baseline hash", lambda r: r["candidates"][0].update(canonical_baseline_parameter_hash="0" * 64))
    reg("classification", lambda r: r["candidates"][0].update(phase2_classification="LOCAL_SPIKE"))
    reg("removed", lambda r: r["candidates"].pop())
    reg("fifth", lambda r: r["candidates"].append(copy.deepcopy(r["candidates"][0])))
    reg("duplicate study", lambda r: r["candidates"][1].update(strategy="T2", timeframe="M30"))
    reg("mutable", lambda r: r.update(immutable=False))
    reg("selection unlocked", lambda r: r["candidates"][0].update(selection_locked_before_validation=False))
    reg("validation used", lambda r: r["candidates"][0].update(validation_data_used_for_selection=True))
    man("ranking", lambda m: m.update(ranking_executed=True))
    reg("robustness", lambda r: r["candidates"][0].update(robustness_executed=True))
    reg("oos unblocked", lambda r: r["candidates"][0].update(true_oos_blocked=False))
    reg("reference merge", lambda r: r["candidates"][0].update(phase2_reference_merge="bad"))
    reg("strategy hash", lambda r: r["candidates"][0].update(frozen_strategy_source_hash="0" * 64))
    man("artifact sha", lambda m: m["artifact_sha256"].update({"Candidate_Freeze_Report.md": "0" * 64}))
    return cases


def test_canonical_audit_passes(tmp_path):
    output = generate(ROOT, tmp_path)
    assert audit(ROOT, output / "candidate_registry.json", output / "manifest.json", output / "Candidate_Freeze_Report.md")["audit"] == "PASS"


def test_all_required_tamper_mutations_fail_closed(tmp_path):
    canonical = generate(ROOT, tmp_path / "canonical")
    registry = json.loads((canonical / "candidate_registry.json").read_text())
    manifest = json.loads((canonical / "manifest.json").read_text())
    for index, (label, changed_registry, changed_manifest) in enumerate(mutations(registry, manifest)):
        output = tmp_path / str(index); output.mkdir()
        (output / "Candidate_Freeze_Report.md").write_bytes((canonical / "Candidate_Freeze_Report.md").read_bytes())
        _write_bundle(output, changed_registry, changed_manifest)
        with pytest.raises(AssertionError, match="."):
            audit(ROOT, output / "candidate_registry.json", output / "manifest.json", output / "Candidate_Freeze_Report.md")
