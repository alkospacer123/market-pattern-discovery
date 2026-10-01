"""Order-free Intel host preflight; use --offline for reproducible CI checks."""
import argparse,json,shutil,socket,sqlite3,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
try: from .operations import InstanceLock
except ImportError: from operations import InstanceLock

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
def run(offline:bool,state_directory:Path)->dict:
    checks={"python":sys.version_info >= (3,11),"sqlite":sqlite3.sqlite_version_info >= (3,35)}
    state_directory.mkdir(parents=True,exist_ok=True)
    probe=state_directory/".write-probe"; probe.write_text("ok"); probe.unlink(); checks["state_directory_writable"]=True
    checks["disk_space"] = shutil.disk_usage(state_directory).free >= 100*1024*1024
    with InstanceLock(state_directory/"stage8.lock"): checks["single_instance_lock"]=True
    if offline: checks["finam_network"]="SKIPPED_OFFLINE"; checks["clock_sanity"]="LOCAL_UTC_ONLY"
    else:
        socket.create_connection(("api.finam.ru",443),timeout=5).close(); checks["finam_network"]=True
        checks["clock_sanity"]=datetime.now(timezone.utc).utcoffset().total_seconds()==0
    stage8=subprocess.run([sys.executable,str(HERE/"audit_stage8.py"),"--check-only"],cwd=ROOT,capture_output=True,text=True)
    stage7=subprocess.run([sys.executable,str(ROOT/"TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze/audit_production_specification.py"),"--check-only"],cwd=ROOT,capture_output=True,text=True)
    checks["stage8_audit_pass"]=stage8.returncode==0; checks["stage7_authentication_pass"]=stage7.returncode==0
    registry=(HERE/"production_instrument_registry.csv").read_text(); checks["registry_safe_state"]=(registry.count("BLOCKED_UNAUTHENTICATED")==4 or registry.count("AUTHENTICATED_REAL_READONLY")==4)
    failed=[k for k,v in checks.items() if v is False]
    return {"status":"PASS" if not failed else "FAIL","offline":offline,"checks":checks,"failures":failed,
            "live_trading_authorized":False}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--offline",action="store_true"); p.add_argument("--state-directory",type=Path,required=True); a=p.parse_args()
    result=run(a.offline,a.state_directory); print(json.dumps(result,sort_keys=True)); raise SystemExit(result["status"]!="PASS")
if __name__=="__main__": main()
