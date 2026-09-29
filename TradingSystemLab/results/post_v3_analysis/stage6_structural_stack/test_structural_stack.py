from pathlib import Path
import pandas as pd
from .generate_structural_stack import session_eligible
from . import generate_structural_stack as gen

def test_session_boundaries():
    assert not session_eligible(pd.Timestamp('2024-01-01 09:59',tz='Europe/Moscow'))
    assert session_eligible(pd.Timestamp('2024-01-01 10:00',tz='Europe/Moscow'))
    assert session_eligible(pd.Timestamp('2024-01-01 20:59',tz='Europe/Moscow'))
    assert not session_eligible(pd.Timestamp('2024-01-01 21:00',tz='Europe/Moscow'))

def test_lock_is_next_event_and_only_tightens():
    assert gen.base.lock_levels('LONG',100,10,115,True)==(115,False)
    assert gen.base.lock_levels('LONG',100,10,105,True)==(110,True)
    assert gen.base.lock_levels('SHORT',100,10,85,True)==(85,False)
    assert gen.base.lock_levels('SHORT',100,10,95,True)==(90,True)

def test_generated_stack_coexists_causally_and_exits_outside_session():
    p=Path(__file__).parent/'structural_stack_v1_trades.csv'
    if not p.exists(): return
    x=pd.read_csv(p); reached=x[x.reached_2r.astype(bool)]
    assert (pd.to_datetime(reached.first_lock1_active_event,utc=True)>pd.to_datetime(reached.trigger_event_time,utc=True)).all()
    exit_hours=pd.to_datetime(x.exit_time,utc=True).dt.tz_convert('Europe/Moscow').dt.hour
    assert ((exit_hours<10)|(exit_hours>=21)).any()
    assert (x.exit_reason=='LOCK1_STOP').any()

def test_no_contaminating_rule_state():
    registry=pd.read_csv(Path(__file__).parent/'structural_stack_registry.csv')
    assert set(registry.rule)=={'FULL_CANONICAL','SESSION_10_21 + LOCK1_AFTER_2R'}
