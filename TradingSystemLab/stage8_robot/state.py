"""Transactional SQLite state and idempotency ledger."""
import json,sqlite3
from pathlib import Path
from typing import Any
class StateStore:
    def __init__(self,path:Path, identity:dict|None=None):
        self.db=sqlite3.connect(path); self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE IF NOT EXISTS intents(idempotency_key TEXT PRIMARY KEY,payload TEXT NOT NULL,status TEXT NOT NULL); CREATE TABLE IF NOT EXISTS fills(fill_id TEXT PRIMARY KEY,payload TEXT NOT NULL);")
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
            cur=self.db.execute("INSERT OR IGNORE INTO intents VALUES(?,?,?)",(key,json.dumps(payload,sort_keys=True),"INTENT_PERSISTED"))
        return cur.rowcount==1
    def intent(self,key:str):
        row=self.db.execute("SELECT payload,status FROM intents WHERE idempotency_key=?",(key,)).fetchone()
        return ({"payload":json.loads(row[0]),"status":row[1]} if row else None)
