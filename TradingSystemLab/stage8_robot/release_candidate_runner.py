"""Explicit V2 release preview runner: manifest-bound, HALTED, GET-only, once.

No authorization creation/loading, task, kill switch, deploy or order interface.
Normal production_service CLI remains legacy unless this manifest path is given.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from .execution_grid import EXECUTION_REVISION, FINAM_FILL_AUTHORITY_VERIFIED
from .finam_api import FinamAPI
from .production_service import ProductionService
from .release_preparation import ReleaseBlocked, digest, flat_broker, validate_manifest


class CandidateReadonlyAPI(FinamAPI):
    """HTTP allowlist independent of the production entry gate or token power."""
    def __init__(self,secret,account_id,**kwargs):
        super().__init__(secret,**kwargs)
        self.account_id=account_id
        self.path='/v1/accounts/'+quote(account_id,safe='')
        self.bound=False
    def _request(self,method,path,payload=None,auth=True,retries=0):
        session=method=='POST' and path in {'/v1/sessions','/v1/sessions/details'}
        read=method=='GET' and self.bound and payload is None and path in {self.path,self.path+'/orders'}
        if not session and not read:raise ReleaseBlocked('CANDIDATE_READONLY_REQUEST_FORBIDDEN')
        return super()._request(method,path,payload,auth,retries)
    def connect_readonly(self):
        self.create_session();details=self.session_details()
        ids=details.get('account_ids') if isinstance(details,dict) else None
        if not isinstance(ids,list) or ids.count(self.account_id)!=1 or details.get('readonly') is not True:
            raise ReleaseBlocked('EXACT_READONLY_SESSION_REQUIRED')
        self.bound=True


def run_preview(runtime_root,data_root, *, manifest,manifest_sha,accepted_commit,secret,account_id,
                api_factory=None,clock=None):
    """The actual ProductionService selects V2; transport stays structurally absent."""
    validate_manifest(manifest,manifest_sha,runtime_root=runtime_root,data_root=data_root,
                      account_hash=digest(account_id),accepted_commit=accepted_commit)
    if FINAM_FILL_AUTHORITY_VERIFIED is not False:
        raise ReleaseBlocked('CLOSED_CANDIDATE_ENTRY_GUARD_REQUIRED')
    api=(api_factory or CandidateReadonlyAPI)(secret,account_id)
    api.connect_readonly()
    svc=ProductionService(runtime_root,data_root,api,account_id,accepted_commit,
                          execution_revision=EXECUTION_REVISION,clock=clock)
    try:
        now=(clock() if clock else datetime.now(timezone.utc)).astimezone(timezone.utc)
        snap=svc.snapshot(now)
        flat_broker({'observed_at':now.isoformat(),'account':snap.account,
                     'orders':{'orders':[{'order_id':r.order_id,'status':r.status,
                         'order' if r.kind=='REGULAR' else 'sltp_order':r.request} for r in snap.orders]}},digest(account_id))
        svc._assert_exact_broker_ownership(snap)
        if svc.transport is not None or svc.runtime.store.unresolved_intent_count() or not svc.runtime.store.get('execution_halt'):
            raise ReleaseBlocked('ORDER_INCAPABLE_HALTED_PREVIEW_REQUIRED')
        return {'status':'V2_SELECTED_READONLY_HALTED_PASS','execution_revision':svc.runtime.execution_revision,
                'selected_service':'ProductionService','accepted_commit':accepted_commit,
                'entry_authorized':False,'live_production_ready':'NO','real_order_endpoint_calls':0,
                'broker_account_hash':svc.account_hash,'live_changes':'NONE'}
    finally:svc.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description='Manifest-bound, isolated V2 GET-only preview')
    for flag in ('runtime-root','stage5-data-root','release-manifest'):
        parser.add_argument('--'+flag,type=Path,required=True)
    parser.add_argument('--release-manifest-sha256',required=True)
    parser.add_argument('--accepted-commit',required=True)
    args=parser.parse_args(argv)
    from .production_service import run_from_environment
    try:
        return run_from_environment(args.runtime_root,args.stage5_data_root,accepted_commit=args.accepted_commit,
            once=True,release_manifest=args.release_manifest,release_manifest_sha256=args.release_manifest_sha256)
    except (RuntimeError,ValueError) as exc:
        print(str(exc));return 1


if __name__=='__main__':raise SystemExit(main())
