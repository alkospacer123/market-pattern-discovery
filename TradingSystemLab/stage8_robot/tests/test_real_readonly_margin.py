import json
from decimal import Decimal
from pathlib import Path
import pytest
from TradingSystemLab.stage8_robot.broker import FinamRealReadOnlyBroker,OrderRequest
from TradingSystemLab.stage8_robot.config import RuntimeConfig,RuntimeMode
from TradingSystemLab.stage8_robot.margin import (MarginBatchBudget,cap_r15_by_margin,
    directional_initial_margin,floor_to_trade_lot,forts_funds,margin_capacity,parse_money)
from TradingSystemLab.stage8_robot.operations import InstanceLock,sqlite_backup,write_heartbeat
from TradingSystemLab.stage8_robot.runner import RobotRunner

FIXTURE=Path("TradingSystemLab/stage8_robot/tests/real_account_fixture.json")
def fixture(): return json.loads(FIXTURE.read_text())

@pytest.mark.parametrize("money,expected",[
 ({"currency_code":"RUB","units":"12","nanos":0},Decimal("12")),
 ({"currency_code":"RUB","units":"12","nanos":500000000},Decimal("12.5")),
 ({"currency_code":"RUB","units":"0","nanos":0},Decimal("0")),
 ({"currency_code":"RUB","units":"-2","nanos":-500000000},Decimal("-2.5"))])
def test_exact_money_parser(money,expected): assert parse_money(money)==expected
@pytest.mark.parametrize("money,error",[
 ({"currency_code":"RUB","units":1,"nanos":0},"MALFORMED_MONEY_UNITS"),
 ({"currency_code":"RUB","units":"1","nanos":"0"},"MALFORMED_MONEY_NANOS"),
 ({"currency_code":"USD","units":"1","nanos":0},"MARGIN_CURRENCY_MISMATCH"),
 ({"currency_code":"RUB","units":"1"},"MALFORMED_MONEY"),
 ({"currency_code":"RUB","units":"-1","nanos":500000000},"MALFORMED_MONEY_SIGN")])
def test_money_parser_fails_closed(money,error):
    with pytest.raises(ValueError,match=error): parse_money(money)
def test_forts_and_directional_margin_exact_shapes():
    data=fixture(); assert forts_funds(data["account"])==(Decimal("200000.25"),Decimal("1000"))
    assert directional_initial_margin(data["asset_params"],"LONG")==Decimal("12000.5")
    assert directional_initial_margin(data["asset_params"],"SHORT")==Decimal("13000.75")
    with pytest.raises(ValueError,match="FORTS_PORTFOLIO_MISSING"): forts_funds({})
    bad=fixture()["asset_params"]; bad["long_initial_margin"].update(units="-1",nanos=0)
    with pytest.raises(ValueError,match="NON_POSITIVE_MARGIN"): directional_initial_margin(bad,"LONG")

@pytest.mark.parametrize("risk,free,margin,lot,final",[(1,"100","10",1,1),(5,"20","10",1,2),(3,"30","10",1,3),(0,"100","10",1,0),(3,"0","10",1,0),(7,"100","10",3,6)])
def test_margin_cap_never_increases_or_rounds_up(risk,free,margin,lot,final):
    x=cap_r15_by_margin(realized_equity=Decimal("1000"),entry=Decimal("100"),stop=Decimal("90"),price_step=Decimal("1"),tick_value=Decimal("1"),r15_quantity=risk,available_cash=Decimal(free),direction="LONG",initial_margin=Decimal(margin),trade_lot_size=lot)
    assert x.final_quantity==final and x.final_quantity<=risk and x.final_quantity%lot==0
def test_natural_small_medium_and_larger_quantities():
    assert [margin_capacity(Decimal(x),Decimal("100"),1) for x in ("99","100","350")]==[0,1,3]
def test_direction_can_change_capacity():
    p=fixture()["asset_params"]; assert margin_capacity(Decimal("25000"),directional_initial_margin(p,"LONG"),1)==2
    assert margin_capacity(Decimal("25000"),directional_initial_margin(p,"SHORT"),1)==1
def test_same_event_budget_reserves_locally():
    budget=MarginBatchBudget(Decimal("250")); args=dict(realized_equity=Decimal("100000"),entry=Decimal("100"),stop=Decimal("90"),price_step=Decimal("1"),tick_value=Decimal("1"),r15_quantity=5,direction="LONG",initial_margin=Decimal("100"),trade_lot_size=1)
    assert budget.size_and_reserve(**args).final_quantity==2
    assert budget.size_and_reserve(**args).final_quantity==0 and budget.remaining==Decimal("50")

class FakeAPI:
    def create_session(self): return {}
    def session_details(self): return {"readonly":True,"account_ids":["real"]}
    def account(self,_): return fixture()["account"]
    def orders(self,_): return {"orders":[]}
def test_real_readonly_adapter_requires_readonly_and_never_submits():
    broker=FinamRealReadOnlyBroker(FakeAPI(),"real"); broker.connect()
    with pytest.raises(RuntimeError,match="REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED"): broker.submit_order(OrderRequest("x","x","LONG",1))
def test_real_mode_requires_separate_account(monkeypatch):
    monkeypatch.setenv("FINAM_MODE","REAL_READONLY"); monkeypatch.setenv("FINAM_REAL_ACCOUNT_ID","real"); monkeypatch.delenv("FINAM_DEMO_ACCOUNT_ID",raising=False); monkeypatch.delenv("STARTING_REALIZED_EQUITY",raising=False)
    assert RuntimeConfig.from_environment().mode is RuntimeMode.FINAM_REAL_READONLY

def real_config(path): return RuntimeConfig(path,path.with_suffix(".jsonl"),None,"none",RuntimeMode.FINAM_REAL_READONLY,False,"real")
def test_clean_real_account_bootstraps_once_and_ignores_later_broker_equity(tmp_path):
    broker=FinamRealReadOnlyBroker(FakeAPI(),"real"); first=RobotRunner(real_config(tmp_path/"s.db"),broker); first.startup()
    assert first.realized_equity==Decimal("250000.5") and first.entries_enabled is False
    data=fixture(); data["account"]["equity"]["value"].update(units="999999",nanos=0)
    data["account"]["unrealized_profit"]["value"].update(units="749998",nanos=500000000)
    api=FakeAPI(); api.account=lambda _:data["account"]
    second=RobotRunner(real_config(tmp_path/"s.db"),FinamRealReadOnlyBroker(api,"real")); second.startup()
    assert second.realized_equity==Decimal("250000.5")
    second.book_exit(Decimal("100"),Decimal("2"),Decimal("1")); assert second.realized_equity==Decimal("250097.5")
def test_dirty_real_account_cannot_initialize(tmp_path):
    data=fixture(); data["account"]["positions"]=[{"contract_id":"manual","quantity":1}]
    api=FakeAPI(); api.account=lambda _:data["account"]
    with pytest.raises(RuntimeError,match="REAL_ACCOUNT_NOT_CLEAN_FOR_INITIALIZATION"): RobotRunner(real_config(tmp_path/"s.db"),FinamRealReadOnlyBroker(api,"real")).startup()
@pytest.mark.parametrize("contamination",["position","order"])
def test_existing_account_contamination_fails_closed(tmp_path,contamination):
    data=fixture(); api=FakeAPI()
    if contamination=="position": data["account"]["positions"]=[{"contract_id":"unrelated","quantity":1}]
    else: api.orders=lambda _:{"orders":[{"order_id":"manual"}]}
    api.account=lambda _:data["account"]
    with pytest.raises(RuntimeError,match="REAL_ACCOUNT_NOT_CLEAN_FOR_INITIALIZATION"): RobotRunner(real_config(tmp_path/f"{contamination}.db"),FinamRealReadOnlyBroker(api,"real")).startup()
def test_unexplained_equity_discrepancy_blocks_restart(tmp_path):
    config=real_config(tmp_path/"s.db"); RobotRunner(config,FinamRealReadOnlyBroker(FakeAPI(),"real")).startup()
    data=fixture(); data["account"]["equity"]["value"]["units"]="250001"; api=FakeAPI(); api.account=lambda _:data["account"]
    with pytest.raises(RuntimeError,match="UNEXPLAINED_REALIZED_EQUITY_DISCREPANCY"): RobotRunner(config,FinamRealReadOnlyBroker(api,"real")).startup()

def test_instance_lock_backup_and_sanitized_heartbeat(tmp_path):
    with InstanceLock(tmp_path/"robot.lock"):
        with pytest.raises(RuntimeError,match="SECOND_ROBOT_INSTANCE_BLOCKED"): InstanceLock(tmp_path/"robot.lock").acquire()
    import sqlite3
    source=tmp_path/"s.db"; db=sqlite3.connect(source); db.execute("create table x(v)"); db.execute("insert into x values(1)"); db.commit()
    dest=sqlite_backup(source,tmp_path/"backups/b.sqlite3"); assert sqlite3.connect(dest).execute("select * from x").fetchone()==(1,)
    heartbeat=tmp_path/"heartbeat.json"; write_heartbeat(heartbeat,mode="REAL_READONLY",production_id="p",account_hash="hash",last_completed_h1=None,last_api_contact=None,reconciliation_status="RECONCILED",entries_enabled=False,unresolved_order_count=0)
    assert "secret" not in heartbeat.read_text().lower()
