#!/usr/bin/env python3
"""Independent fail-closed audit against canonical Stage 1 source evidence."""
import csv, hashlib, json, math, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
TOL=1e-9

def rows(path):
    p=path if isinstance(path,Path) else HERE/path
    with p.open(newline="",encoding="utf-8") as f: return list(csv.DictReader(f))

def close(a,b): return math.isclose(float(a),float(b),rel_tol=TOL,abs_tol=TOL)
def key(r): return tuple(r[x] for x in ("generation","lifecycle_stage","strategy","timeframe"))

def assert_period_report(stage_rows, source_path):
    source=rows(source_path); by_month={r["YYYY-MM"]:r for r in stage_rows}
    assert set(by_month)=={r["month"] for r in source}, f"month coverage mismatch: {source_path}"
    for expected in source:
        actual=by_month[expected["month"]]
        aliases=(("trades","total_trades"),("PF","PF"),("expectancy_R","expectancy"),("net_R","net_R"),("max_drawdown_R","max_drawdown"),("win_rate","win_rate"))
        for output_col, source_col in aliases:
            if source_col in expected and expected[source_col] not in ("", "NA"):
                assert close(actual[output_col],expected[source_col]), f"monthly {source_path} {expected['month']} {output_col}"

def main():
    source=(HERE/"generate.py").read_text(encoding="utf-8")
    assert "canonical_c1_r" in source and "development_or_phase2" not in source
    assert not any(x in source for x in ("core.data_loader","core.strategy","optimization.","pandas.read_"))
    manifest=json.loads((HERE/"manifest.json").read_text())
    assert manifest["status"]=="POST_V3_STAGE_1_MASTER_EVIDENCE_COMPLETE"
    assert all(manifest["controls"][x] for x in ("C1_normalization_verified","phase2_candidate_metrics_verified","canonical_aggregate_reconciliation","deterministic_rerun"))
    for item in manifest["source_files_used"]:
        p=ROOT/item["path"]; assert p.is_file(); assert hashlib.sha256(p.read_bytes()).hexdigest()==item["sha256"]

    master=rows("master_study_comparison.csv"); assert len(master)==36
    assert {r["lifecycle_stage"] for r in master}=={"baseline","walk_forward","true_oos"}
    keys=[key(r) for r in master]; assert len(keys)==len(set(keys))
    indexed={key(r):r for r in master}
    inst=rows("instrument_statistics.csv"); direct=rows("direction_statistics.csv"); monthly=rows("chronological_monthly_statistics.csv")
    for m in master:
        k=key(m); n=int(m["total_trades"]); net=float(m["net_R"])
        ii=[r for r in inst if key(r)==k]; dd=[r for r in direct if key(r)==k]; mm=[r for r in monthly if key(r)==k]
        assert sum(int(r["total_trades"]) for r in ii)==n and sum(int(r["trades"]) for r in dd)==n and sum(int(r["trades"]) for r in mm)==n
        assert close(sum(float(r["net_R"]) for r in ii),net) and close(sum(float(r["net_R"]) for r in dd),net) and close(sum(float(r["net_R"]) for r in mm),net)
        periods=[r["YYYY-MM"] for r in mm]; assert periods==sorted(periods) and len(periods)==len(set(periods))

    # Known C1 controls: these fail if the old C0 reconstruction returns.
    controls={
      ("v1","walk_forward","T3","H1"):(34,3.3803276720178377,.9679913199721701,32.91170487905379,-5.038562132510952),
      ("v1","walk_forward","T2","H1"):(33,3.2479236097361213,.816803426096776,26.95451306119361,-3.498691117514663)}
    for k,expected in controls.items():
        r=indexed[k]; actual=(int(r["total_trades"]),*[float(r[x]) for x in ("PF","expectancy_R","net_R","max_drawdown_R")])
        assert actual[0]==expected[0] and all(close(a,b) for a,b in zip(actual[1:],expected[1:])), f"C1 regression {k}"
        if k[2]=="T3": assert not close(r["PF"],3.49197193021), "C0 PF leaked into Stage 1"

    phase2={
      ("v2","T2","M30"):(1.38439307062,.179005404674,-33.5282069751),("v2","T2","H1"):(1.49070753729,.224423840621,-14.9346837251),
      ("v2","T3","M30"):(1.36261268342,.162875006507,-22.5343558886),("v2","T3","H1"):(1.46328578667,.203160457152,-16.2129477802),
      ("v3","T2","M30"):(1.7118816595,.310463258155,-16.3334012952),("v3","T2","H1"):(2.39295957746,.575052042961,-6.88205022139),
      ("v3","T3","M30"):(1.93094457407,.376193476605,-15.012134415),("v3","T3","H1"):(2.31342650378,.399304363394,-5.67342240555),
      ("v1","T2","H1"):(2.24786524529,.532454866083,-9.72662840455),("v1","T3","H1"):(2.05031716776,.463442957611,-16.7839035694)}
    for identity, expected in phase2.items():
        r=indexed[(identity[0],"baseline",identity[1],identity[2])]
        actual=[r[x] for x in ("phase2_candidate_PF","phase2_candidate_expectancy_R","phase2_candidate_max_drawdown_R")]
        assert all(close(a,b) for a,b in zip(actual,expected)), f"Phase 2 regression {identity}"

    wf={k:v for k,v in {
      ("v1","T2","M30"):"WALK_FORWARD_BORDERLINE",("v1","T3","M30"):"WALK_FORWARD_PASS",("v1","T2","H1"):"WALK_FORWARD_BORDERLINE",("v1","T3","H1"):"WALK_FORWARD_BORDERLINE",
      **{(g,s,t):("WALK_FORWARD_PASS" if (g,s,t)==("v3","T3","H1") else "WALK_FORWARD_BORDERLINE") for g in ("v2","v3") for s in ("T2","T3") for t in ("M30","H1")}}.items()}
    oos={('v1','T2','M30'):'BORDERLINE',('v1','T3','M30'):'PASS',('v1','T2','H1'):'PASS',('v1','T3','H1'):'PASS',
         **{(g,s,t):('PASS' if g=='v3' and s=='T3' else 'BORDERLINE') for g in ('v2','v3') for s in ('T2','T3') for t in ('M30','H1')}}
    for (g,s,t),verdict in wf.items(): assert indexed[(g,"walk_forward",s,t)]["classification"]==verdict
    for (g,s,t),verdict in oos.items(): assert indexed[(g,"true_oos",s,t)]["classification"]==verdict

    for s in ("T2","T3"):
        assert_period_report([r for r in monthly if key(r)==("v1","true_oos",s,"M30")],ROOT/f"TradingSystemLab/results/true_oos_validation/M30/{s}/monthly_report.csv")
        for tf in ("M30","H1"):
            assert_period_report([r for r in monthly if key(r)==("v3","true_oos",s,tf)],ROOT/f"TradingSystemLab/results/perpetual_v3/true_oos/{s}/{tf}/monthly_report.csv")

    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
    subprocess.run([sys.executable,str(HERE/"generate.py")],check=True)
    after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
    assert before==after,"outputs are not byte-deterministic"
    print(f"PASS: {len(master)} studies; canonical C1/Phase 2/verdict/period reconciliation; deterministic rerun")

if __name__=="__main__": main()
