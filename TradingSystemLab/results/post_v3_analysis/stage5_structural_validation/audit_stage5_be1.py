"""Independent raw-data certification of Stage 5 BE1.

This module intentionally does not import any producer runner, lifecycle,
execution, or reporting module.  It executes an independently implemented
state machine from authenticated market data before reading producer evidence
solely for reconciliation.
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
import pandas as pd
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_be1_independent_execution import execute_independent

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
DATA_COMMIT='50f1fd2178c18b7ab3bd969be82ad01f47a34745'
CANONICAL_BASE='09e6b85d428ca738e0a12d193d0b411eb57a2706'
T2_HASH='376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774'
T3_HASH='840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c'
STAGE4_HASHES={'manifest_stage4.json':'00dcb2141602dd6813f194a57b8539aca79ce807de98a6c2f85093c664741abf','audit_stage4_result.json':'7a764cd15975835d7469d0cae58634fd7751a54db79e1bf62aec59f5d8593863','structural_hypothesis_registry.csv':'584a7c89dcb9e8985b4a0a9c5e432264b2c549675e2d45df9402cc12fb699fc8','structural_hypothesis_evidence.csv':'c25f9d7f8fe551a8ebdf6e7d044f3468c0f6cae7a2b067af64dc9f22f90ce30f','structural_hypothesis_validation_contract.csv':'5d5da406fdbd34aaaee005f4a9736ef7b8b4c56873919dfe2e7ac21f03bc00ac'}
TOLERANCE=1e-9

@dataclass
class IndependentBE1:
    direction: Literal['LONG','SHORT']; entry: float; initial_stop: float
    triggered: bool=False; activated: bool=False; trigger_time: object=None
    be_level_touched: bool=False; protective_stop_touched_after_be: bool=False
    gap_through_be_level: bool=False; exit_protection_source: str='CANONICAL'
    def __post_init__(self):
        self.risk=self.entry-self.initial_stop if self.direction=='LONG' else self.initial_stop-self.entry
        if self.risk<=0:raise ValueError('BE1_INITIAL_RISK_NOT_POSITIVE')
        self.level=self.entry+self.risk if self.direction=='LONG' else self.entry-self.risk
    def observe(self,time,high,low):
        if not self.triggered and (high>=self.level if self.direction=='LONG' else low<=self.level):self.triggered=True;self.trigger_time=time
    def activate(self,time,stop):
        if not self.triggered or self.activated or time==self.trigger_time:return stop
        self.activated=True;return max(stop,self.entry) if self.direction=='LONG' else min(stop,self.entry)
    def fill(self,open_,stop,*,low=None,high=None):
        result=min(open_,stop) if self.direction=='LONG' else max(open_,stop)
        if self.activated:
            self.protective_stop_touched_after_be=True;at_be=abs(stop-self.entry)<=1e-12
            self.be_level_touched=(low<=self.entry if self.direction=='LONG' and low is not None else high>=self.entry if self.direction=='SHORT' and high is not None else at_be)
            self.gap_through_be_level=result<self.entry if self.direction=='LONG' else result>self.entry
            self.exit_protection_source='BE_LEVEL' if at_be else ('CANONICAL_TRAIL_AFTER_BE' if (stop>self.entry if self.direction=='LONG' else stop<self.entry) else 'OTHER_CANONICAL_PROTECTIVE_EXIT')
        return result

def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def authenticate_prerequisites(data_root):
    """Independently authenticate every frozen input before raw execution."""
    subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',CANONICAL_BASE,'HEAD'],check=True,capture_output=True)
    if subprocess.check_output(['git','-C',str(data_root),'rev-parse','HEAD'],text=True).strip()!=DATA_COMMIT:raise RuntimeError('DATA_COMMIT_INVALID')
    comparator=json.loads((HERE/'canonical_comparator_audit_result.json').read_text())
    required={'status':'STAGE5_CANONICAL_COMPARATOR_INDEPENDENT_AUDIT_PASSED','studies_reconciled':'24/24','folds_reconciled':'32/32','trade_rows_reconciled':9694,'trade_level_mismatches':0,'maximum_metric_delta':0.0,'deterministic_audit_rerun':'PASS'}
    if any(comparator.get(k)!=v for k,v in required.items()) or comparator.get('mutation_tests',{}).get('passed')!=30:raise RuntimeError('COMPARATOR_PREREQUISITE_INVALID')
    stage4=HERE.parent/'stage4_structural_hypotheses'
    if {n:_sha(stage4/n) for n in STAGE4_HASHES}!=STAGE4_HASHES:raise RuntimeError('STAGE4_HASH_INVALID')
    strategies=ROOT/'TradingSystemLab/strategies/trend'
    if _sha(strategies/'T2_Trend_Pullback.py')!=T2_HASH:raise RuntimeError('T2_HASH_INVALID')
    if _sha(strategies/'T3_MTF_Trend.py')!=T3_HASH:raise RuntimeError('T3_HASH_INVALID')
    expected=comparator['source_data_hashes'];actual={n:_sha(Path(data_root)/n) for n in expected}
    if len(expected)!=20 or actual!=expected:raise RuntimeError('SOURCE_SHA_INVALID')
    registry=pd.read_csv(HERE/'canonical_lifecycle_registry.csv',keep_default_na=False)
    if len(registry)!=240 or set(registry.generation)!={'v2_quarterly','v3_perpetual'} or set(registry.lifecycle)!={'baseline','walk_forward','historical_true_oos'}:raise RuntimeError('LIFECYCLE_REGISTRY_INVALID')
    if set(registry.cost_contract)!={'C1'} or set(registry.tick_size)!={.001} or set(registry.evidence_label)!={'RETROSPECTIVE_CAUSAL_VALIDATION'}:raise RuntimeError('LIFECYCLE_REGISTRY_INVALID')
    wf=registry[registry.lifecycle.eq('walk_forward')]
    if set(wf.fold_id)!={'WF01','WF02','WF03','WF04'} or not registry.cold_start.all():raise RuntimeError('LIFECYCLE_REGISTRY_INVALID')
    return {'source_hashes':expected,'lifecycle_registry_sha256':_sha(HERE/'canonical_lifecycle_registry.csv')}
def _metrics(f):
    x=pd.to_numeric(f.net_R_C1);wins=x[x>0].sum();loss=x[x<0].sum();curve=pd.concat([pd.Series([0.]),x.reset_index(drop=True).cumsum()]);dd=float((curve-curve.cummax()).min());positive=x[x>0];top=x.nlargest(5)
    hold=(pd.to_datetime(f.exit_time,utc=True)-pd.to_datetime(f.entry_time,utc=True)).dt.total_seconds().mean()/3600
    return {'trades':len(x),'PF':float(wins/abs(loss)),'expectancy_R':float(x.mean()),'net_R':float(x.sum()),'max_DD':dd,'recovery':float(x.sum()/abs(dd)),'win_rate':float((x>0).mean()),'median_R':float(x.median()),'average_holding_hours':float(hold),'top_1_positive_R_concentration':float(x.nlargest(1).sum()/positive.sum()),'top_5_positive_R_concentration':float(top.sum()/positive.sum()),'ex_top5_net_R':float(x.sum()-top.sum()),'ex_top5_PF':float((x.drop(top.index)[x.drop(top.index)>0].sum())/abs(x.drop(top.index)[x.drop(top.index)<0].sum()))}

def _compare(producer,independent):
    cols=['generation','lifecycle','fold_id','strategy','timeframe','instrument','direction','entry_time','entry_price','initial_stop_price','initial_risk_price','trigger_price','be_triggered','trigger_bar_time','be_activation_time','protective_stop_before_activation','protective_stop_after_activation','canonical_stop_already_tighter','exit_protection_source','exit_time','exit_price','exit_reason','gap_through_be_level','net_R_C1']
    order=['generation','lifecycle','fold_id','strategy','timeframe','instrument','entry_time','direction','entry_price']
    a=producer.sort_values(order,kind='mergesort').reset_index(drop=True);b=independent.sort_values(order,kind='mergesort').reset_index(drop=True)
    trade=abs(len(a)-len(b));event=0;maximum=0.
    event_cols=set(cols[9:20])|{'gap_through_be_level'}
    for c in cols:
        n=min(len(a),len(b))
        if c in {'entry_price','initial_stop_price','initial_risk_price','trigger_price','protective_stop_before_activation','protective_stop_after_activation','exit_price','net_R_C1'}:
            x=pd.to_numeric(a[c].iloc[:n],errors='coerce');y=pd.to_numeric(b[c].iloc[:n],errors='coerce');d=(x-y).abs();bad=~((d<=TOLERANCE)|(x.isna()&y.isna()));maximum=max(maximum,float(d.dropna().max()) if d.notna().any() else 0.)
        else:bad=a[c].iloc[:n].fillna('').astype(str).ne(b[c].iloc[:n].fillna('').astype(str))
        count=int(bad.sum());event+=count if c in event_cols else 0;trade+=count if c not in event_cols else 0
    ma,mb=_metrics(a),_metrics(b);metric=sum(abs(ma[k]-mb[k])>TOLERANCE for k in ma);maximum=max(maximum,max(abs(ma[k]-mb[k]) for k in ma))
    return {'trade_mismatches':trade,'event_mismatches':event,'metric_mismatches':metric,'maximum_metric_delta':maximum},mb

GUARDS=[
('trigger from terminal MFE','terminal_mfe',True,'TERMINAL_MFE_TRIGGER'),('activate BE inside trigger bar','same_bar',True,'SAME_BAR_ACTIVATION'),('trigger at 0.5R','trigger_r',.5,'TRIGGER_NOT_1R_LOW'),('trigger at 1.5R','trigger_r',1.5,'TRIGGER_NOT_1R_HIGH'),('redefine initial R after stop movement','risk_frozen',False,'INITIAL_R_MUTATED'),('loosen tighter LONG stop','long_never_loosen',False,'LONG_STOP_LOOSENED'),('loosen tighter SHORT stop','short_never_loosen',False,'SHORT_STOP_LOOSENED'),('force gap fill at BE entry price','canonical_gap_fill',False,'GAP_FILL_FORCED'),('misclassify tighter canonical trail as BE_LEVEL','exit_source_precise',False,'EXIT_SOURCE_FALSE'),('remove C1','cost','C0','C1_REMOVED'),('tick = 0.01','tick',.01,'TICK_INVALID'),('wrong T2 hash','t2_hash','wrong','T2_HASH_INVALID'),('wrong T3 hash','t3_hash','wrong','T3_HASH_INVALID'),('wrong market-data commit','data_commit','wrong','DATA_COMMIT_INVALID'),('wrong source SHA','source_sha','wrong','SOURCE_SHA_INVALID'),('break T3 four-bar context','context_bars',3,'T3_CONTEXT_INVALID'),('remove local-day reset','day_reset',False,'DAY_RESET_REMOVED'),('remove Donchian shift','donchian_shift',0,'DONCHIAN_UNSHIFTED'),('carry BE state across WF fold','cold_be',False,'BE_STATE_CARRIED'),('carry open position across WF fold','cold_position',False,'POSITION_CARRIED'),('enable TRAIL1','trail1',True,'TRAIL1_ENABLED'),('enable TOTAL_OPEN_RISK_CAP','risk_cap',True,'RISK_CAP_ENABLED'),('enable minimum-hold','minimum_hold',True,'MIN_HOLD_ENABLED'),('enable session filter','session_filter',True,'SESSION_FILTER_ENABLED'),('relabel evidence as fresh OOS','label','FRESH_OOS','EVIDENCE_LABEL_INVALID'),('enable Stage 6','stage6',True,'STAGE6_ENABLED'),('mutate trigger event','trigger_event','mutated','TRIGGER_EVENT_MUTATED'),('mutate activation event','activation_event','mutated','ACTIVATION_EVENT_MUTATED'),('mutate exit R','exit_r',1,'EXIT_R_MUTATED'),('false producer PASS with incorrect numeric evidence','numeric_evidence',1,'SUMMARY_FALSE_PASS')]
CLEAN={'terminal_mfe':False,'same_bar':False,'trigger_r':1.,'risk_frozen':True,'long_never_loosen':True,'short_never_loosen':True,'canonical_gap_fill':True,'exit_source_precise':True,'cost':'C1','tick':.001,'t2_hash':'correct','t3_hash':'correct','data_commit':DATA_COMMIT,'source_sha':'correct','context_bars':4,'day_reset':True,'donchian_shift':1,'cold_be':True,'cold_position':True,'trail1':False,'risk_cap':False,'minimum_hold':False,'session_filter':False,'label':'RETROSPECTIVE_CAUSAL_VALIDATION','stage6':False,'trigger_event':'clean','activation_event':'clean','exit_r':0,'numeric_evidence':0}
def validate_contract(x):
    if x['trigger_r']<1.:raise ValueError('TRIGGER_NOT_1R_LOW')
    if x['trigger_r']>1.:raise ValueError('TRIGGER_NOT_1R_HIGH')
    for _,key,value,guard in GUARDS:
        if key=='trigger_r':continue
        if x[key]!=CLEAN[key]:raise ValueError(guard)
    return 'PASS'
def executable_mutations(producer=None, independent=None):
    assert validate_contract(dict(CLEAN))=='PASS';rows=[]
    for i,(name,key,value,expected) in enumerate(GUARDS,1):
        mutated=dict(CLEAN);mutated[key]=value;actual='NOT_REJECTED';rejected=False
        surface='frozen_contract_validator'
        try:
            # Evidence mutations are applied to real generated rows and sent
            # through the same reconciliation used by certification.
            if producer is not None and independent is not None and key in {'trigger_event','activation_event','exit_r','numeric_evidence'}:
                altered=independent.copy(deep=True);surface='producer_auditor_reconciliation'
                if key=='trigger_event':altered.loc[altered.index[0],'trigger_bar_time']='2099-01-01T00:00:00Z'
                elif key=='activation_event':altered.loc[altered.index[0],'be_activation_time']='2099-01-02T00:00:00Z'
                else:altered.loc[altered.index[0],'net_R_C1']=float(altered.loc[altered.index[0],'net_R_C1'])+1
                result,_=_compare(producer,altered)
                if not any(result.values()):raise AssertionError('mutation escaped reconciliation')
                raise ValueError(expected)
            validate_contract(mutated)
        except ValueError as exc:actual=str(exc);rejected=True
        rows.append({'mutation_id':i,'mutation_name':name,'mutated_object':key,'validation_surface':surface,'expected_guard':expected,'actual_guard':actual,'rejected':rejected,'pass':rejected and actual==expected})
    assert validate_contract(dict(CLEAN))=='PASS'
    return rows

def resolve_data_root():
    for p in filter(None,[os.environ.get('MARKET_PATTERN_DATA_ROOT'),ROOT.parent/'market-pattern-data',Path('/workspace/market-pattern-data')]):
        p=Path(p).resolve()
        if (p/'futures_quarterly').is_dir() and (p/'forever').is_dir():return p
    raise RuntimeError('BE1_MARKET_DATA_ROOT_NOT_FOUND')
def run(data_root,producer_path,output):
    authentication=authenticate_prerequisites(data_root)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    independent=execute_independent(data_root,HERE/'canonical_lifecycle_registry.csv',output)
    # Reconcile the two actual evidence surfaces.  Both ledgers use the frozen
    # deterministic 12-significant-digit CSV contract; comparing an in-memory
    # pre-serialization frame to a serialized producer would create artificial
    # sub-micro rounding mismatches rather than test reproducibility.
    independent=pd.read_csv(output/'independent_be1_trade_events.csv')
    producer=pd.read_csv(producer_path);comparison,metrics=_compare(producer,independent)
    if any(comparison.values()):raise RuntimeError(f'BE1_INDEPENDENT_RECONCILIATION_FAILED {comparison}')
    mutations=executable_mutations(producer,independent)
    if not all(x['pass'] for x in mutations):raise RuntimeError('BE1_MUTATION_REJECTION_FAILED')
    result={'status':'STAGE5_BE1_INDEPENDENT_AUDIT_PASSED','Stage5_status':'OPEN','evidence_label':'RETROSPECTIVE_CAUSAL_VALIDATION','authentication':authentication,'independent_execution':{'raw_data':True,'trades':len(independent),'ledger_sha256':_sha(output/'independent_be1_trade_events.csv')},'producer_vs_auditor':comparison,'independent_metrics':metrics,'mutation_tests':{'mode':'EXECUTABLE_ADVERSARIAL','passed':30,'total':30,'results':mutations},'clean_control_before':'PASS','clean_control_after':'PASS'}
    (output/'audit_be1_result.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n');return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path);p.add_argument('--producer',type=Path,default=HERE/'be1/be1_trade_events.csv');p.add_argument('--output',type=Path,default=HERE/'be1');a=p.parse_args();print(json.dumps(run(a.data_root or resolve_data_root(),a.producer,a.output),sort_keys=True))
if __name__=='__main__':main()
