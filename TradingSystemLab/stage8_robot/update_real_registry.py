"""Atomic registry promotion from externally validated REAL_READONLY evidence."""
import csv,hashlib,json,os,tempfile
from pathlib import Path
from .instrument_resolver import N4,evidence_sha256
def update(evidence_path:Path,registry_path:Path):
    report=json.loads(evidence_path.read_text()); bindings=report.get("bindings",{})
    if (report.get("binding_status")!="AUTHENTICATED_REAL_READONLY" or report.get("token_readonly") is not True
        or report.get("account_clean") is not True or tuple(sorted(bindings))!=tuple(sorted(N4))
        or any(x.get("status")!="AUTHENTICATED_REAL_READONLY" for x in bindings.values())
        or report.get("evidence_sha256")!=evidence_sha256(bindings)):
        raise RuntimeError("REAL_READONLY_ACTIVATION_REQUIRES_VALIDATED_ALL_FOUR")
    rows=list(csv.DictReader(registry_path.open(newline="",encoding="utf-8"))); fields=list(rows[0])
    for row in rows: row["binding_status"]="AUTHENTICATED_REAL_READONLY"
    fd,name=tempfile.mkstemp(dir=registry_path.parent,prefix="registry-",suffix=".tmp"); os.close(fd); temp=Path(name)
    try:
        with temp.open("w",newline="",encoding="utf-8") as out:
            writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader(); writer.writerows(rows)
        os.replace(temp,registry_path)
    finally: temp.unlink(missing_ok=True)
