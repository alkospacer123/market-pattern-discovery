import json
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from .specification import PRODUCTION_SPECIFICATION_ID
class AuditLogger:
    def __init__(self,path:Path): self.path=path
    def write(self,event:str,**fields:Any):
        record={"timestamp":datetime.now(timezone.utc).isoformat(),"production_specification_id":PRODUCTION_SPECIFICATION_ID,"strategy":"T3","configuration":"T3-H1-4e73cdb77246","variant":"TRAIL1","event":event,**fields}
        with self.path.open("a",encoding="utf-8") as f: f.write(json.dumps(record,sort_keys=True,default=str)+"\n")
