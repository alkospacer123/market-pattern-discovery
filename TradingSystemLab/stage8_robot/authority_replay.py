"""Isolated research-authority replay (never imported by production replay)."""
from dataclasses import replace
import json
from pathlib import Path
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3Parameters
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_lifecycle import run_t3

ROOT=Path(__file__).resolve().parents[2]
CONFIGURATION="T3-H1-4e73cdb77246"

def frozen_parameters():
    registry=json.loads((ROOT/"TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze/candidate_registry.json").read_text())
    row=next(x for x in registry["candidates"] if x["strategy"]=="T3" and x["timeframe"]=="H1")
    if row["phase2_configuration_id"]!=CONFIGURATION: raise RuntimeError("CANDIDATE_IDENTITY_MISMATCH")
    return replace(T3Parameters(),**row["parameters"])

def replay_authority(frame,symbol,meta):
    """Stage-6 baseline semantic: candidate parameters, baseline interval/label."""
    return run_t3(frame,symbol,frozen_parameters(),{"generation":"v3_perpetual","strategy":"T3","timeframe":"H1",
                  "candidate_config_identity":CONFIGURATION,**meta},True)
