import argparse
from datetime import datetime,timezone
from pathlib import Path
try: from .operations import prune_backups,sqlite_backup
except ImportError: from operations import prune_backups,sqlite_backup
def main():
    p=argparse.ArgumentParser(); p.add_argument("source",type=Path); p.add_argument("backup_directory",type=Path); p.add_argument("--keep",type=int,default=14); a=p.parse_args()
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(sqlite_backup(a.source,a.backup_directory/f"stage8-{stamp}.sqlite3")); prune_backups(a.backup_directory,a.keep)
if __name__=="__main__": main()
