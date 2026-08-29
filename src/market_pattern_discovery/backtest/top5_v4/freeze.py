from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from datetime import date,datetime
import math
import numpy as np
import pandas as pd
from .common import canonical_json

def file_sha256(path):
    h=sha256();
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def _semantic_scalar(value):
    if value is None or value is pd.NA:return None
    if isinstance(value,(pd.Timestamp,datetime,date)):return value.isoformat()
    if isinstance(value,np.generic):value=value.item()
    if isinstance(value,float):
        if math.isnan(value):return None
        if math.isinf(value):return "INF" if value>0 else "-INF"
    return value
def semantic_ledger_hash(ledger):
    if ledger.empty:return sha256(b"[]").hexdigest()
    # A selected ledger is a semantic projection of the full multi-family union.
    # Family-specific columns contributed by *unselected* families can survive
    # pandas concat as columns that are null in every selected row.  Those empty
    # union-schema columns are not trade semantics and must not make DEV freeze
    # hashes depend on which unrelated families were present in the full grid.
    cols=sorted(c for c in ledger.columns if not ledger[c].isna().all());x=ledger[cols].copy();sort_cols=[c for c in ("candidate_id","signal_id","trade_id","friction") if c in x]
    if sort_cols:x=x.sort_values(sort_cols,kind="mergesort")
    records=[{c:_semantic_scalar(v) for c,v in row.items()} for row in x.to_dict("records")];return sha256(canonical_json(records).encode()).hexdigest()
def freeze_manifest(engine_commit,contract_path,registry_path,dependency_versions,selected_path,dev_ledger_path,environments,data_hashes,access_ledger_path,selected_dev_semantic_ledger_hash,code_hashes=None):
    return {"engine_commit":engine_commit,"contract_sha256":file_sha256(contract_path),"candidate_registry_sha256":file_sha256(registry_path),"selected_sha256":file_sha256(selected_path),"dev_ledger_file_sha256":file_sha256(dev_ledger_path),"selected_dev_semantic_ledger_hash":selected_dev_semantic_ledger_hash,"code_hashes":code_hashes or {},"dependency_versions":dependency_versions,"environments":environments,"data_hashes":data_hashes,"access_ledger_sha256":file_sha256(access_ledger_path),"manifest_semantics":"engine commit E is committed clean engine; generated DEV/freeze artifacts may live in child commit F"}
def verify_frozen_manifest(manifest,paths):
    for key,path in paths.items():
        if file_sha256(path)!=manifest[key]:raise ValueError(f"freeze hash mismatch: {key}")
