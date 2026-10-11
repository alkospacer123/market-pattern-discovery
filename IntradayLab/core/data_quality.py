"""Prospective M5 policy and explicit result; legacy tuple API stays unchanged."""
from dataclasses import dataclass

LEGACY_UNKNOWN = 'LEGACY_UNKNOWN'
DATA_GAP_SKIP_V2 = 'DATA_GAP_SKIP_V2'


@dataclass
class DataQualityResult:
    signals: list
    trades: list
    days: list
    data_gap_skips: list
    data_quality_exclusions: list
    data_gap_policy: str = DATA_GAP_SKIP_V2

    def validate(self):
        """Fail before reporting if an accepted entry is lost or counted twice."""
        key = lambda r: (r['instrument'], r['signal_id'])
        ledgers = (self.signals, self.trades, self.data_gap_skips,
                   self.data_quality_exclusions)
        for rows in ledgers:
            if len({key(r) for r in rows}) != len(rows):
                raise ValueError('DUPLICATE_SIGNAL_OR_OUTCOME')
        fills = {key(s) for s in self.signals if s['model_filled']}
        closed = {key(t) for t in self.trades}
        excluded = {key(t) for t in self.data_quality_exclusions}
        skipped = {key(s) for s in self.data_gap_skips}
        if closed & excluded or fills != closed | excluded or skipped & fills:
            raise ValueError('ACCEPTED_ENTRY_RECONCILIATION')
        if skipped != {key(s) for s in self.signals if s['status']=='DATA_GAP_SKIP'}:
            raise ValueError('SKIP_RECONCILIATION')
        if any(t['status']!='CLOSED' for t in self.trades):
            raise ValueError('ONLY_CLOSED_IN_TRADE_LEDGER')
        if any(t['status']!='DATA_QUALITY_EXCLUDED' or not t['model_filled']
               for t in self.data_quality_exclusions):
            raise ValueError('EXCLUSION_MUST_RETAIN_FILL')
        if any(t.get(k) is not None for t in self.data_quality_exclusions for k in (
                'exit_price', 'exit_at', 'resolved_at', 'gross', 'gross_R',
                'net_c1', 'net_R_c1', 'cost_c1', 'cost_R')):
            raise ValueError('EXCLUSION_CANNOT_HAVE_ECONOMIC_OUTCOME')
        if any(r.get('status')=='UNKNOWN' for rows in ledgers for r in rows):
            raise ValueError('LEGACY_STATUS_IN_V2')
        return self
