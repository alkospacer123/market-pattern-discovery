from __future__ import annotations
import copy, json, tempfile, unittest
from pathlib import Path
from freeze_production_specification import CORE_FILES, generate
from audit_production_specification import audit

class FreezeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)/"base"; generate(self.root)
 def tearDown(self): self.tmp.cleanup()
 def mutate(self, fn):
  p=self.root/"production_specification.json"; x=json.loads(p.read_text()); fn(x); p.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n"); self.assertEqual(audit(self.root,False)["status"],"FAIL")
 def test_deterministic_isolated_generation_and_audit(self):
  other=Path(self.tmp.name)/"other"; self.assertEqual(generate(self.root),generate(other)); self.assertEqual(audit(self.root,False)["status"],"PASS"); self.assertEqual(audit(other,False)["status"],"PASS")
  for n in CORE_FILES:self.assertEqual((self.root/n).read_bytes(),(other/n).read_bytes(),n)
 def test_semantic_mutations(self):
  mutations=[lambda x:x.update(identity="CANONICAL__N4_01__FULL__R15"),lambda x:x["basket"]["instruments"].pop(),lambda x:x["basket"]["instruments"].append("Si"),lambda x:x["strategy"].update(timeframe="M30"),lambda x:x["risk"].update(risk_fraction_per_new_instrument_position=.02),lambda x:x["risk"].update(load="NORMALIZED"),lambda x:x["risk"].update(maximum_nominal_simultaneous_initial_risk=.05),lambda x:x["strategy"].update(source_sha256="0"*64),lambda x:x["strategy"].update(parameter_sha256="0"*64),lambda x:x["variant"].update(source_sha256="0"*64),lambda x:x.update(event_order=list(reversed(x["event_order"]))),lambda x:x["schedule"].update(entry_time_filter="SESSION_10_21"),lambda x:x["variant"].update(forbidden_overlays=[z for z in x["variant"]["forbidden_overlays"] if z!="LOCK1_AFTER_2R"]),lambda x:x.update(status="STABLE_REFERENCE_NOT_ACTIVE_PRODUCTION"),lambda x:x.update(identity="TRAIL1__N4_01__FULL__R20"),lambda x:x.update(production_specification_id="PROD_STAGE7_BAD"),lambda x:x["cost_evidence_contract"].update(name="C0")]
  for i,m in enumerate(mutations):
   with self.subTest(mutation=i): generate(self.root); self.mutate(m)
 def test_reference_and_r20_registry_mutations(self):
  for replacement in ("ACTIVE_PRODUCTION_SPECIFICATION","TRAIL1__N4_01__FULL__R20"):
   generate(self.root); p=self.root/"production_identity_registry.csv"; s=p.read_text(); s=s.replace("STABLE_REFERENCE_NOT_ACTIVE_PRODUCTION",replacement) if replacement.startswith("ACTIVE") else s+f"{replacement},ACTIVE_PRODUCTION_SPECIFICATION,,,\n"; p.write_text(s); self.assertEqual(audit(self.root,False)["status"],"FAIL")
if __name__=="__main__":unittest.main()
