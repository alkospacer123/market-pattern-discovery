"""Host operations with no broker order capabilities."""
from __future__ import annotations
import json,logging,logging.handlers,os,sqlite3,threading
from datetime import datetime,timezone
from pathlib import Path

_PROCESS_LOCKS:set[str]=set(); _LOCK_GUARD=threading.Lock()
class InstanceLock:
    def __init__(self,path:Path): self.path=Path(path); self.stream=None
    def acquire(self):
        key=str(self.path.resolve()); self.path.parent.mkdir(parents=True,exist_ok=True)
        with _LOCK_GUARD:
            if key in _PROCESS_LOCKS: raise RuntimeError("SECOND_ROBOT_INSTANCE_BLOCKED")
            self.stream=self.path.open("a+b")
            try:
                if os.name=="nt":
                    import msvcrt
                    self.stream.seek(0); self.stream.write(b"0"); self.stream.flush(); self.stream.seek(0)
                    msvcrt.locking(self.stream.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(self.stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            except (OSError,IOError):
                self.stream.close(); self.stream=None; raise RuntimeError("SECOND_ROBOT_INSTANCE_BLOCKED") from None
            _PROCESS_LOCKS.add(key)
        return self
    def release(self):
        if self.stream is None:return
        key=str(self.path.resolve())
        try:
            if os.name=="nt":
                import msvcrt
                self.stream.seek(0); msvcrt.locking(self.stream.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(),fcntl.LOCK_UN)
        finally:
            self.stream.close(); self.stream=None
            with _LOCK_GUARD:_PROCESS_LOCKS.discard(key)
    def __enter__(self): return self.acquire()
    def __exit__(self,*_): self.release()

def sqlite_backup(source:Path,destination:Path)->Path:
    """Consistent online backup, followed by an integrity check."""
    source=Path(source); destination=Path(destination); destination.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst: src.backup(dst)
    with sqlite3.connect(destination) as check:
        if check.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            destination.unlink(missing_ok=True); raise RuntimeError("SQLITE_BACKUP_INTEGRITY_FAILED")
    return destination

def prune_backups(directory:Path,keep:int)->list[Path]:
    if keep<1: raise ValueError("BACKUP_RETENTION_INVALID")
    files=sorted(Path(directory).glob("*.sqlite3"),key=lambda p:p.stat().st_mtime,reverse=True)
    for old in files[keep:]: old.unlink()
    return files[:keep]

def configure_operational_log(path:Path,max_bytes:int=5_000_000,backup_count:int=5)->logging.Logger:
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    logger=logging.getLogger("stage8.operations"); logger.setLevel(logging.INFO); logger.handlers.clear()
    logger.addHandler(logging.handlers.RotatingFileHandler(path,maxBytes=max_bytes,backupCount=backup_count,encoding="utf-8"))
    return logger

def write_heartbeat(path:Path,*,mode:str,production_id:str,account_hash:str,last_completed_h1:str|None,
                    last_api_contact:str|None,reconciliation_status:str,entries_enabled:bool,
                    unresolved_order_count:int):
    payload={"timestamp":datetime.now(timezone.utc).isoformat(),"mode":mode,"production_id":production_id,
             "account_hash":account_hash,"last_completed_h1_timestamp":last_completed_h1,
             "last_successful_finam_api_contact":last_api_contact,"reconciliation_status":reconciliation_status,
             "entries_enabled":entries_enabled,"unresolved_order_count":unresolved_order_count}
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True); temp=target.with_suffix(target.suffix+".tmp")
    temp.write_text(json.dumps(payload,sort_keys=True)+"\n",encoding="utf-8"); os.replace(temp,target)

