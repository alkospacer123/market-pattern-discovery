from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import patch
import importlib.util
import json
import pytest
import sys
import types

script = Path(__file__).resolve().parents[1] / 'diagnostics' / 'stage8-493-finam-broker-flat-readonly.py'
spec = importlib.util.spec_from_file_location('readonly_under_test', script)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

@pytest.fixture
def runtime():
    with TemporaryDirectory() as tmp:
        p=Path(tmp)
        (p/'safety').mkdir();(p/'diagnostics').mkdir()
        spec=m.SPEC
        (p/'safety/stage8-trading-kill-switch.json').write_text(json.dumps({'schema_id':'stage8_trading_kill_switch.v1','production_specification_id':spec,'state':'HALTED'}))
        now=datetime.now(timezone.utc).isoformat()
        (p/'diagnostics/stage8-12-4-production-heartbeat.json').write_text(json.dumps({'schema_id':'stage8_12_4_production_heartbeat.v1','production_specification_id':spec,'active_identity':m.IDENTITY,'accepted_code_commit':m.LIVE_SHA,'account_hash':'abc','timestamp':now,'last_successful_finam_api_contact':now,'health_status':'HEALTHY','reconciliation_status':'PASS','open_position_count':0,'unresolved_intent_count':0,'active_protective_stop_count':0,'position_protection':[],'cycle_count':11282}))
        yield p

def test_local_gate_pass_and_fail_closed(runtime):
    assert m.local_gate(runtime,'abc')==11282
    with pytest.raises(m.Blocked,match='ACCOUNT_HASH_MISMATCH'):m.local_gate(runtime,'def')
    sw=runtime/'safety/stage8-trading-kill-switch.json'
    v=json.loads(sw.read_text());v['state']='ARMED';sw.write_text(json.dumps(v))
    with pytest.raises(m.Blocked,match='NEW_ENTRIES_NOT_HALTED'):m.local_gate(runtime,'abc')

def test_broker_flatness_and_active_order_fail_closed():
    positions=lambda a:{} if not a['positions'] else {'other':1}
    views=lambda o:[SimpleNamespace(active=x.get('active',False)) for x in o['orders']]
    account={'account_id':'name','status':'ACCOUNT_ACTIVE','positions':[]}
    assert m.evaluate_broker(account,{'orders':[{'active':False}]},'name',positions,views)['flat']
    assert not m.evaluate_broker(account,{'orders':[{'active':True}]},'name',positions,views)['flat']
    with pytest.raises(m.Blocked,match='FINAM_ACCOUNT_ID_MISMATCH'):m.evaluate_broker(account,{'orders':[]},'other',positions,views)


def test_allowlist_two_broker_observations_and_zero_writes(runtime,monkeypatch,capsys):
    import hashlib
    account='test-account'
    account_hash=hashlib.sha256(account.encode()).hexdigest()
    hb=runtime/'diagnostics/stage8-12-4-production-heartbeat.json'
    x=json.loads(hb.read_text());x['account_hash']=account_hash;hb.write_text(json.dumps(x))

    clients=[]
    class FakeFinamAPI:
        def __init__(self,secret): clients.append(self)
        def create_session(self): self._request('POST','/v1/sessions',auth=False)
        def session_details(self):
            self._request('POST','/v1/sessions/details',auth=False)
            return {'readonly':True,'account_ids':[account]}
        def account(self,a):
            self._request('GET',self.account_path)
            return {'account_id':account,'status':'ACCOUNT_ACTIVE','positions':[]}
        def orders(self,a):
            self._request('GET',self.account_path+'/orders')
            return {'orders':[]}
        def _request(self,method,path,payload=None,auth=True,retries=0): return None
    def pos(a):return {}
    def orders(o):return []
    mods={
        'TradingSystemLab':types.ModuleType('TradingSystemLab'),
        'TradingSystemLab.stage8_robot':types.ModuleType('TradingSystemLab.stage8_robot'),
        'TradingSystemLab.stage8_robot.finam_api':types.SimpleNamespace(FinamAPI=FakeFinamAPI),
        'TradingSystemLab.stage8_robot.production_broker_state':types.SimpleNamespace(position_quantities=pos,order_views=orders),
    }
    with patch.dict(sys.modules,mods),patch.object(m.subprocess,'check_output',return_value=m.LIVE_SHA+'\n'),patch.object(m.time,'sleep'):
        m.run(runtime,Path('/fake-checkout'),secret='fake-readonly',account=account)
    assert 'CLASSIFICATION=FRESH_FINAM_READONLY_FLAT_PASS_NOT_ISOLATED' in capsys.readouterr().out
    assert len(clients)==1
    for method,path in (('POST',clients[0].account_path+'/orders'),('POST',clients[0].account_path+'/sltp-orders'),
                        ('DELETE',clients[0].account_path+'/orders/123'),('GET','/v1/accounts/other/orders'),
                        ('GET',clients[0].account_path+'/trades')):
        with pytest.raises(m.Blocked,match='FINAM_METHOD_OR_ENDPOINT_FORBIDDEN'):
            clients[0]._request(method,path)


def test_ps_no_mutation_actions():
    ps=(Path(__file__).resolve().parents[1]/'diagnostics'/'stage8-493-finam-broker-flat-readonly.ps1').read_text()
    for phrase in ['Stop-ScheduledTask','Disable-ScheduledTask','Enable-ScheduledTask','Get-TradingCredential','Invoke-RestMethod','Set-Content','Set-Acl']:
        assert phrase not in ps
    assert 'Get-ReadonlyCredential' in ps
    assert 'PYTHONDONTWRITEBYTECODE' in ps


def test_heartbeat_fail_closed_on_stale_or_nonzero_positions(runtime):
    hb=runtime/'diagnostics/stage8-12-4-production-heartbeat.json'
    original=json.loads(hb.read_text())
    for field,value in (('open_position_count',1),('unresolved_intent_count',1),('active_protective_stop_count',1),
                        ('health_status','UNHEALTHY'),('reconciliation_status','FAULT'),('accepted_code_commit','f'*40)):
        payload={**original,field:value}
        hb.write_text(json.dumps(payload))
        with pytest.raises(m.Blocked): m.local_gate(runtime,'abc')
    payload={**original,'timestamp':(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()}
    hb.write_text(json.dumps(payload))
    with pytest.raises(m.Blocked,match='HEARTBEAT_OR_FINAM_CONTACT_STALE'):m.local_gate(runtime,'abc')


def test_broker_rejects_nonzero_and_unknown_order_status():
    from types import SimpleNamespace
    account={'account_id':'name','status':'ACCOUNT_ACTIVE','positions':[]}
    with pytest.raises(m.Blocked,match='FINAM_ACCOUNT_NOT_ACTIVE'):
        m.evaluate_broker({**account,'status':'INVALID'}, {'orders':[]},'name',lambda x:{},lambda x:[])
    report=m.evaluate_broker(account,{'orders':[{'status':'NEW'}]},'name',lambda x:{},lambda x:[SimpleNamespace(active=True)])
    assert report['flat'] is False
    report=m.evaluate_broker({**account,'positions':[{'symbol':'CNYRUBF@RTSX','quantity':{'value':'1'}}]}, {'orders':[]},'name',lambda x:{'CNYRUBF@RTSX':1},lambda x:[])
    assert report['flat'] is False
