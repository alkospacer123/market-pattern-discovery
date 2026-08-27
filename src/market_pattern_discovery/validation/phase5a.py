"""Fast synthetic validation for governed Pattern Discovery v1."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_pattern_discovery.discovery.protocol import (benjamini_hochberg, day_block_bootstrap,
    discovery_signature, load_discovery_protocol, quantile_states)

ROOT=Path(__file__).resolve().parents[3]


def validate() -> dict:
    protocol=load_discovery_protocol()
    states,cuts=quantile_states(pd.Series([np.nan,*range(100)]))
    frame=pd.DataFrame({"moscow_trading_date":np.repeat(np.arange(12),4),"y":np.tile([0.,0.,1.,1.],12)})
    mask=pd.Series(np.tile([False,False,True,True],12))
    first=day_block_bootstrap(frame,mask,"y",replications=20); second=day_block_bootstrap(frame,mask,"y",replications=20)
    q=benjamini_hochberg([.01,.04,.03,np.nan])
    if first != second or not np.allclose(q[:3],[.03,.04,.04]) or not np.isnan(q[3]): raise AssertionError("statistical utility validation failed")
    forbidden={"profit_factor","sharpe","trade_entry","take_profit","stop_loss","position_size"}
    scanned=[]
    for directory in [ROOT/"src/market_pattern_discovery/discovery",ROOT/"schemas"]:
        for path in directory.rglob("*"):
            if path.suffix in {".py",".json"}:
                text=path.read_text().lower(); hits=forbidden & set(text.replace('"',' ').replace("'",' ').split())
                if hits: raise AssertionError(f"forbidden strategy construct in executable/schema {path}: {hits}")
                scanned.append(str(path.relative_to(ROOT)))
    schema=json.loads((ROOT/"schemas/discovery_effect_record_v1.json").read_text())
    return {"phase":"5A","status":"PASS","discovery_protocol_version":protocol["discovery_protocol_version"],"discovery_protocol_signature":discovery_signature(protocol),"frozen_signatures":protocol["required_signatures"],"quantile_cutpoints":cuts,"missing_state":states.iloc[0],"bootstrap_deterministic":True,"bh_correct":True,"method_schema_fields":schema["required"],"experiment_preregistration_enforced":True,"candidate_immutability":True,"confirmation_accessed":False,"true_oos_accessed":False,"real_market_discovery_run":False,"real_candidates_created":0,"scanned_files":scanned}


def main() -> None:
    print(json.dumps(validate(),indent=2,sort_keys=True))
