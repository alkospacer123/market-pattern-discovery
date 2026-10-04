"""Transactional SQLite state and the isolated Stage 8.11 ledger authority."""
import hashlib,json,os,sqlite3,tempfile
from pathlib import Path
from typing import Any
from .specification import PRODUCTION_SPECIFICATION_ID

TERMINAL_INTENT_STATUSES=("CANCELLED","REJECTED","CLOSED","RECONCILED")
SUPERVISOR_DATABASE = "readonly-supervisor.sqlite3"
STAGE8_11_ACCEPTANCE_DATABASE = "stage8-11-acceptance.sqlite3"
STAGE8_11_BROKER_AUTHORITY = "FINAM"
STAGE8_11_REAL_ENVIRONMENT = "STAGE8_11_REAL_ACCEPTANCE"

_SCHEMA = """CREATE TABLE state(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE intents(idempotency_key TEXT PRIMARY KEY,payload TEXT NOT NULL,status TEXT NOT NULL,broker_order_id TEXT,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE fills(fill_id TEXT PRIMARY KEY,broker_order_id TEXT NOT NULL,trade_id TEXT NOT NULL,quantity TEXT NOT NULL,price TEXT NOT NULL,fee TEXT,timestamp TEXT NOT NULL,payload TEXT NOT NULL);"""

def stage8_11_acceptance_path(runtime_root:Path)->Path:
    return Path(runtime_root)/"state"/STAGE8_11_ACCEPTANCE_DATABASE

def stage8_11_identity(account_id:str)->dict[str,str]:
    if not account_id: raise ValueError("STAGE8_11_ACCOUNT_ID_REQUIRED")
    return {"production_specification_id":PRODUCTION_SPECIFICATION_ID,
            "broker_authority":STAGE8_11_BROKER_AUTHORITY,
            "account_sha256":hashlib.sha256(account_id.encode("utf-8")).hexdigest(),
            "environment":STAGE8_11_REAL_ENVIRONMENT}

def _validate_acceptance_database(path:Path,identity:dict[str,str])->None:
    connection=sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
    try:
        tables={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables != {"state","intents","fills"}: raise sqlite3.DatabaseError("ACCEPTANCE_SCHEMA_INVALID")
        expected={
          "state":("key","value"),
          "intents":("idempotency_key","payload","status","broker_order_id","updated_at"),
          "fills":("fill_id","broker_order_id","trade_id","quantity","price","fee","timestamp","payload")}
        if any(tuple(r[1] for r in connection.execute(f"PRAGMA table_info({table})")) != columns for table,columns in expected.items()):
            raise sqlite3.DatabaseError("ACCEPTANCE_SCHEMA_INVALID")
        row=connection.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
        if row is None or json.loads(row[0]) != identity: raise RuntimeError("STATE_ENVIRONMENT_ACCOUNT_MISMATCH")
        if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",): raise sqlite3.DatabaseError("ACCEPTANCE_INTEGRITY_INVALID")
    finally: connection.close()

def initialize_stage8_11_acceptance_ledger(runtime_root:Path,account_id:str)->Path:
    """Create once, or validate without mutation, the canonical local ledger."""
    path=stage8_11_acceptance_path(runtime_root); supervisor=path.with_name(SUPERVISOR_DATABASE)
    if path.resolve()==supervisor.resolve(): raise RuntimeError("ACCEPTANCE_SUPERVISOR_AUTHORITY_COLLISION")
    identity=stage8_11_identity(account_id)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        _validate_acceptance_database(path,identity); return path
    fd,name=tempfile.mkstemp(prefix=path.name+".",suffix=".incomplete",dir=path.parent); os.close(fd)
    temporary=Path(name)
    try:
        connection=sqlite3.connect(temporary)
        try:
            connection.executescript(_SCHEMA)
            connection.execute("INSERT INTO state(key,value) VALUES(?,?)",("database_identity",json.dumps(identity,sort_keys=True)))
            connection.commit(); connection.execute("PRAGMA wal_checkpoint(FULL)")
        finally: connection.close()
        _validate_acceptance_database(temporary,identity)
        # Never replace an authority that appeared concurrently.
        try: os.link(temporary,path)
        except FileExistsError: _validate_acceptance_database(path,identity)
        else: os.unlink(temporary)
        _validate_acceptance_database(path,identity); return path
    finally: temporary.unlink(missing_ok=True)

def readonly_unresolved_intent_count(path:Path)->int:
    """Read the canonical ledger without creating or modifying it."""
    path=path.resolve()
    if not path.is_file(): raise FileNotFoundError(path)
    connection=sqlite3.connect(path.as_uri()+"?mode=ro",uri=True)
    try:
        columns={row[1] for row in connection.execute("PRAGMA table_info(intents)")}
        required={"idempotency_key","payload","status","broker_order_id","updated_at"}
        if not required.issubset(columns): raise sqlite3.DatabaseError("INTENTS_SCHEMA_INVALID")
        marks=",".join("?" for _ in TERMINAL_INTENT_STATUSES)
        row=connection.execute(f"SELECT COUNT(*) FROM intents WHERE status NOT IN ({marks})",TERMINAL_INTENT_STATUSES).fetchone()
        if row is None or type(row[0]) is not int: raise sqlite3.DatabaseError("INTENTS_COUNT_INVALID")
        return row[0]
    finally: connection.close()
class StateStore:
    def __init__(self,path:Path, identity:dict|None=None):
        self.db=sqlite3.connect(path); self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(_SCHEMA.replace("CREATE TABLE ","CREATE TABLE IF NOT EXISTS "))
        if identity is not None:
            current=self.get("database_identity")
            if current is not None and current != identity: raise RuntimeError("STATE_ENVIRONMENT_ACCOUNT_MISMATCH")
            self.put("database_identity",identity)
    def put(self,key:str,value:Any):
        with self.db: self.db.execute("INSERT INTO state VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,json.dumps(value,sort_keys=True)))
    def get(self,key:str,default=None):
        row=self.db.execute("SELECT value FROM state WHERE key=?",(key,)).fetchone(); return json.loads(row[0]) if row else default
    def persist_intent(self,key:str,payload:dict)->bool:
        with self.db:
            cur=self.db.execute("INSERT OR IGNORE INTO intents(idempotency_key,payload,status) VALUES(?,?,?)",(key,json.dumps(payload,sort_keys=True),"INTENT_PERSISTED"))
        return cur.rowcount==1
    def intent(self,key:str):
        row=self.db.execute("SELECT payload,status,broker_order_id FROM intents WHERE idempotency_key=?",(key,)).fetchone()
        return ({"payload":json.loads(row[0]),"status":row[1],"broker_order_id":row[2]} if row else None)
    def transition_intent(self,key:str,status:str,broker_order_id:str|None=None):
        allowed={"INTENT_PERSISTED","SUBMITTED","UNCERTAIN","ACK","PARTIAL_FILL","FILL","CANCELLED","REJECTED","CLOSED","RECONCILED"}
        if status not in allowed: raise ValueError("INVALID_ORDER_STATUS")
        with self.db:
            cur=self.db.execute("UPDATE intents SET status=?,broker_order_id=COALESCE(?,broker_order_id),updated_at=CURRENT_TIMESTAMP WHERE idempotency_key=?",(status,broker_order_id,key))
            if cur.rowcount!=1: raise KeyError(key)
    def persist_fill(self,fill:dict)->bool:
        required=("fill_id","broker_order_id","trade_id","quantity","price","timestamp")
        if any(k not in fill for k in required): raise ValueError("INCOMPLETE_FILL")
        values=(fill["fill_id"],fill["broker_order_id"],fill["trade_id"],str(fill["quantity"]),str(fill["price"]),str(fill.get("fee","")),fill["timestamp"],json.dumps(fill,sort_keys=True))
        with self.db: cur=self.db.execute("INSERT OR IGNORE INTO fills VALUES(?,?,?,?,?,?,?,?)",values)
        return cur.rowcount==1
    def unresolved_intent_count(self)->int:
        marks=",".join("?" for _ in TERMINAL_INTENT_STATUSES)
        return self.db.execute(f"SELECT COUNT(*) FROM intents WHERE status NOT IN ({marks})",TERMINAL_INTENT_STATUSES).fetchone()[0]
    def close(self): self.db.close()
