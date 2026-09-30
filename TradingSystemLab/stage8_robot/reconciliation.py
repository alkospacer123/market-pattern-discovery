from enum import Enum
class Reconciliation(str,Enum):
    RECONCILED="RECONCILED"; POSITION_MISMATCH="POSITION_MISMATCH"; ORDER_MISMATCH="ORDER_MISMATCH"
    STATE_MISSING="STATE_MISSING"; UNKNOWN_BROKER_POSITION="UNKNOWN_BROKER_POSITION"; UNKNOWN_LOCAL_POSITION="UNKNOWN_LOCAL_POSITION"
def reconcile(local_positions:list[dict]|None,broker_positions:list[dict],local_orders:list[dict],broker_orders:list[dict])->Reconciliation:
    if local_positions is None: return Reconciliation.STATE_MISSING
    lk={p["contract_id"]:p.get("quantity") for p in local_positions}; bk={p["contract_id"]:p.get("quantity") for p in broker_positions}
    if bk.keys()-lk.keys(): return Reconciliation.UNKNOWN_BROKER_POSITION
    if lk.keys()-bk.keys(): return Reconciliation.UNKNOWN_LOCAL_POSITION
    if lk!=bk: return Reconciliation.POSITION_MISMATCH
    if {o["order_id"] for o in local_orders}!={o["order_id"] for o in broker_orders}: return Reconciliation.ORDER_MISMATCH
    return Reconciliation.RECONCILED
