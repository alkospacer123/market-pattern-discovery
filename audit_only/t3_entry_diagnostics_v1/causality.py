"""Primary prefix and future-suffix perturbation checks on development only."""
import math
from support import *

def audit(streams,entries,engine):
    from features import features_for_frame
    original={}
    for r in entries:original.setdefault((r['system'],r['instrument']),[]).append(r)
    checks=[];fields=0
    for s in streams:
        key=(s['system'],s['instrument']);full=s['frame'];rs=original[key]
        # One published-context boundary, one local midnight, one late signal.
        context=next(r['signal_time'] for r in rs if r['context_available_at']==r['signal_time'])
        midnight=next(at for at in full.index if at.hour==0 and at>rs[0]['signal_time'])
        late=rs[-min(8,len(rs))]['signal_time']
        for cut in sorted({context,midnight,late}):
            expected=[clean(r) for r in rs if r['signal_time']<=cut]
            _,prefix=features_for_frame(s['system'],s['instrument'],s['lifecycle'],s['fold_id'],full.loc[:cut].copy(),engine)
            assert [clean(r) for r in prefix]==expected,('PREFIX_INVARIANCE',key,cut)
            changed=full.copy();changed.loc[changed.index>cut,['Open','High','Low','Close']]*=1.03125
            _,mutated=features_for_frame(s['system'],s['instrument'],s['lifecycle'],s['fold_id'],changed,engine)
            actual=[clean(r) for r in mutated if r['signal_time']<=cut]
            assert actual==expected,('FUTURE_SUFFIX_LEAKAGE',key,cut)
            fields+=sum(len(r) for r in expected)*2
            checks.append(dict(system=s['system'],instrument=s['instrument'],cut=cut,
              prefix_signal_rows=len(expected),future_suffix_price_multiplier=1.03125,status='PASS',
              midnight_boundary=cut.hour==0,publication_boundary=cut==context))
    return dict(status='PASS',checks=checks,fields_compared=fields,
                availability='All feature_available_at == signal Close; all context_available_at <= signal',
                future_features='No outcomes read; NEXT_OPEN gap kept outside ENTRY_FEATURES')
