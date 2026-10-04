"""Transactional SQLite state and idempotency ledger."""
import json,sqlite3
from pathlib import Path
from typing import Any
TERMINAL_INTENT_STATUSES=("CANCELLED","REJECTED","CLOSED","RECONCILED")

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
        self.db.executescript("""CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS intents(idempotency_key TEXT PRIMARY KEY,payload TEXT NOT NULL,status TEXT NOT NULL,broker_order_id TEXT,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS fills(fill_id TEXT PRIMARY KEY,broker_order_id TEXT NOT NULL,trade_id TEXT NOT NULL,quantity TEXT NOT NULL,price TEXT NOT NULL,fee TEXT,timestamp TEXT NOT NULL,payload TEXT NOT NULL);""")
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
