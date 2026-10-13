"""Freeze and causal invariants; shared integrity, never diagnostic accounting."""
import json
import common as C

def freeze_guard():
    frozen=json.loads((C.HERE/'FREEZE.json').read_text())
    prefix=C.HERE.relative_to(C.REPO).as_posix()+'/'
    for name,digest in frozen['code_spec_sha256'].items():
        assert C.file_sha(C.HERE/name)==digest,('FROZEN_FILE_CHANGED',name)
        assert C.sha(C.historical(prefix+name,frozen['commit']))==digest,('GIT_FREEZE_CHANGED',name)
    assert not C.git('ls-tree','-r','--name-only',frozen['commit'],'--',prefix+'results').strip(),'RESULTS_BEFORE_FREEZE'
    return frozen

def causal(out):
    checks=0
    entries={(r['instrument'],r['trade_id']):r for r in out['entry_opportunities'] if r['entry_accepted']}
    active={key:r['candidate_initial_stop'] for key,r in entries.items()}
    for trade in out['trades']+out['OPEN_POSITIONS']:
        checks+=1
        entry=entries[(trade['instrument'],trade['trade_id'])]
        assert trade['signal_time']==entry['signal_time']==trade['entry_time']
        assert entry['execution_bar_close']==trade['signal_time']+C.STEP
        assert entry['H1AvailableAt']<=entry['signal_time']
        assert entry['H1ATRRatio']>entry['H1PreviousATRRatio']
        assert abs(trade['initial_risk']-2*entry['ATR'])<=1e-8
    for row in out['stop_decisions']:
        checks+=1
        assert row['bar_close_time']<C.END
        assert row['bar_open_time']+C.STEP==row['bar_close_time']
        key=(row['instrument'],row['trade_id']);side=1 if entries[key]['direction']=='LONG' else -1
        assert abs(row['active_stop']-active[key])<=1e-8
        if row['phase']=='EXIT':
            assert row['stop_hit'] and row['active_stop_next_bar'] is None
            assert not row['threshold_activated_now']
            assert row['activation_time_after']==row['activation_time_before']
            fill=min(row['open'],row['active_stop']) if side==1 else max(row['open'],row['active_stop'])
            assert abs(row['exit_price']-fill)<=1e-8
        elif row['threshold_activated_now']:
            assert not row['stop_hit'] and row['favorable_R_after']>=1.
            assert row['activation_time_after']==row['bar_close_time']
        if row['phase']=='SURVIVED':
            assert not row['stop_hit']
            assert side*(row['active_stop_next_bar']-row['active_stop'])>=-1e-8
            if not row['activated_after']:assert row['active_stop_next_bar']==entries[key]['candidate_initial_stop']
            active[key]=row['active_stop_next_bar']
    assert set(r['instrument'] for r in out['entry_opportunities'])==set(C.SYMBOLS)
    assert len(entries)==len(out['trades'])+len(out['OPEN_POSITIONS'])
    return {'status':'PASS','causal_rows_checked':checks,'executed_entries':len(entries),'CLOSED':len(out['trades']),
            'terminal_OPEN':len(out['OPEN_POSITIONS']),'shared_cross_instrument_limits':False,
            'leave_one_out_method':'arithmetic valid for standalone normalized R; no capital/sizing inference'}
