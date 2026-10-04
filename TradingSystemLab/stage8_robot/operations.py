"""Host operations with no broker order capabilities."""
from __future__ import annotations
import json,logging,logging.handlers,os,sqlite3,threading
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path

_PROCESS_LOCKS:set[str]=set(); _LOCK_GUARD=threading.Lock()
STAGE8_11_EXCLUSIVE_LOCK = Path("locks") / "stage8-11-exclusive.lock"

def stage8_11_exclusive_lock(runtime_root:Path):
    """Return the one OS-backed authority shared by all Stage 8.11 writers."""
    return InstanceLock(Path(runtime_root) / STAGE8_11_EXCLUSIVE_LOCK)

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
    """Create a standalone, checked backup using SQLite's online backup API.

    The source is opened read-only so a typo can never create an empty source.
    A destination is published only after both databases pass integrity checks.
    """
    source=Path(source); destination=Path(destination)
    if not source.is_file() or source.is_symlink():
        raise RuntimeError("SQLITE_BACKUP_SOURCE_INVALID")
    if destination.exists() or destination.resolve()==source.resolve():
        raise RuntimeError("SQLITE_BACKUP_DESTINATION_INVALID")
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_name(destination.name+".incomplete")
    temporary.unlink(missing_ok=True)
    try:
        uri=f"{source.resolve().as_uri()}?mode=ro"
        with closing(sqlite3.connect(uri,uri=True)) as src:
            if src.execute("PRAGMA integrity_check").fetchone()!=("ok",):
                raise RuntimeError("SQLITE_BACKUP_SOURCE_INTEGRITY_FAILED")
            with closing(sqlite3.connect(temporary)) as dst:
                src.backup(dst)
        # The backup is standalone: normalize the copied WAL preference before
        # publication so no sidecar is required to open the recovery point.
        with closing(sqlite3.connect(temporary)) as standalone:
            if standalone.execute("PRAGMA journal_mode=DELETE").fetchone()!=("delete",):
                raise RuntimeError("SQLITE_BACKUP_DESTINATION_INTEGRITY_FAILED")
        with closing(sqlite3.connect(f"{temporary.resolve().as_uri()}?mode=ro",uri=True)) as check:
            if check.execute("PRAGMA integrity_check").fetchone()!=("ok",):
                raise RuntimeError("SQLITE_BACKUP_DESTINATION_INTEGRITY_FAILED")
        os.replace(temporary,destination)
    except (sqlite3.Error,OSError) as exc:
        raise RuntimeError("SQLITE_BACKUP_FAILED") from exc
    finally:
        temporary.unlink(missing_ok=True)
        Path(str(temporary)+"-wal").unlink(missing_ok=True)
        Path(str(temporary)+"-shm").unlink(missing_ok=True)
    return destination

def validate_operational_database(path:Path)->None:
    """Validate the exact schema used by readonly_supervisor.OperationalState."""
    path=Path(path)
    if not path.is_file() or path.is_symlink(): raise RuntimeError("SQLITE_RECOVERY_DATABASE_INVALID")
    try:
        with closing(sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro",uri=True)) as database:
            if database.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise RuntimeError("SQLITE_RECOVERY_INTEGRITY_INVALID")
            tables=database.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            columns=database.execute("PRAGMA table_info(operational_state)").fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError("SQLITE_RECOVERY_DATABASE_INVALID") from exc
    expected=[(0,"key","TEXT",0,None,1),(1,"value","TEXT",1,None,0)]
    if tables != [("operational_state",)] or columns != expected:
        raise RuntimeError("SQLITE_RECOVERY_SCHEMA_INVALID")

def prune_backups(directory:Path,keep:int)->list[Path]:
    """Retain complete ``.sqlite3``/``.manifest.json`` recovery units only."""
    if keep<1: raise ValueError("BACKUP_RETENTION_INVALID")
    directory=Path(directory)
    files=sorted((p for p in directory.glob("*.sqlite3")
                  if p.with_name(p.name+".manifest.json").is_file()),
                 key=lambda p:p.name,reverse=True)
    for old in files[keep:]:
        old.with_name(old.name+".manifest.json").unlink(missing_ok=True); old.unlink(missing_ok=True)
    # Orphans are incomplete operations, never recovery points.
    for database in directory.glob("*.sqlite3"):
        if not database.with_name(database.name+".manifest.json").is_file(): database.unlink(missing_ok=True)
    for manifest in directory.glob("*.sqlite3.manifest.json"):
        database=manifest.with_name(manifest.name.removesuffix(".manifest.json"))
        if not database.is_file(): manifest.unlink(missing_ok=True)
    return files[:keep]

def configure_operational_log(path:Path,max_bytes:int=5_000_000,backup_count:int=5)->logging.Logger:
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    logger=logging.getLogger("stage8.operations"); logger.setLevel(logging.INFO); logger.handlers.clear()
    logger.addHandler(logging.handlers.RotatingFileHandler(path,maxBytes=max_bytes,backupCount=backup_count,encoding="utf-8"))
    return logger

def write_heartbeat(path:Path,*,mode:str,production_id:str,account_hash:str,last_completed_h1:str|None,
                    last_api_contact:str|None,reconciliation_status:str,entries_enabled:bool,
                    unresolved_order_count:int,health_status:str|None=None,
                    failure_code:str|None=None,consecutive_failures:int|None=None,
                    cycle_count:int|None=None):
    payload={"timestamp":datetime.now(timezone.utc).isoformat(),"mode":mode,"production_id":production_id,
             "account_hash":account_hash,"last_completed_h1_timestamp":last_completed_h1,
             "last_successful_finam_api_contact":last_api_contact,"reconciliation_status":reconciliation_status,
             "entries_enabled":entries_enabled,"unresolved_order_count":unresolved_order_count}
    optional={"health_status":health_status,"failure_code":failure_code,
              "consecutive_failures":consecutive_failures,"cycle_count":cycle_count}
    payload.update({key:value for key,value in optional.items() if value is not None})
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True); temp=target.with_suffix(target.suffix+".tmp")
    temp.write_text(json.dumps(payload,sort_keys=True)+"\n",encoding="utf-8"); os.replace(temp,target)
