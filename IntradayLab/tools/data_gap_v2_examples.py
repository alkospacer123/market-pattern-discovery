"""Deterministic synthetic M5 examples, never a strategy Baseline."""
from datetime import date, timedelta
from decimal import Decimal as D
import json
from pathlib import Path

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar
from IntradayLab.core.data_quality import DATA_GAP_SKIP_V2
from IntradayLab.core.execution import ENTRY_NEXT_OPEN
from IntradayLab.core.reports import csv_write, dump, write_data_quality_reports

LAB = Path(__file__).resolve().parents[1]
FIVE = timedelta(minutes=5)


class SyntheticSignals:
    name = 'SYNTHETIC_TECHNICAL_FIXTURE'

    def __init__(self, requests):
        self.requests = requests
        self.observed = []

    def begin_day(self, symbol, day):
        self.symbol = symbol

    def on_bar(self, bar, context):
        self.observed.append((bar, context))
        if bar is None or not bar.valid or context.available_at not in self.requests:
            return []
        return [dict(signal_id=str(context.available_at), signal_at=context.available_at,
                     base_reason='SIGNAL', direction=-1, stop=D('101.02'),
                     target_gross_R='1.5', max_hold_calendar_minutes=60)]

    def end_day(self):
        return []


def fixture():
    config = json.loads((LAB/'config/orb_a_base_2023_canonical_v1.json').read_text())
    config.update(start='2023-01-04', end_exclusive='2023-01-06', instruments=['USDRUBF'])
    rules = MarketRules(config)
    rows = {}
    for day in (date(2023, 1, 4), date(2023, 1, 5)):
        for a, z in rules.windows(day):
            while a < z:
                rows[a] = validate_bar(a, tuple(map(D, ('100.90','100.95','100.80','100.90','10'))),
                                       FIVE, rules.tick('USDRUBF', a))
                a += FIVE
    at = lambda clock, day=date(2023, 1, 4): rules.at(day, clock)
    del rows[at('10:20')]  # skipped entry; no following-Open substitute
    del rows[at('10:50')]  # modeled 10:40 entry has an unverifiable outcome
    for clock, prices in (('11:20', ('100.80','100.95','100.75','100.90','10')),
                          ('13:55', ('100.95','101.00','100.80','100.90','10'))):
        stamp = at(clock, date(2023, 1, 5))
        rows[stamp] = validate_bar(stamp, tuple(map(D, prices)), FIVE, D('.01'))
    requests = [at('10:20'), at('10:40'), at('11:10'),
                at('10:20', date(2023, 1, 5)), at('13:45', date(2023, 1, 5))]
    return config, rules, rows, requests


def generate(output, inputs=None):
    config, rules, rows, requests = inputs if inputs is not None else fixture()
    result = Backtester(rules, entry_mode=ENTRY_NEXT_OPEN,
                        data_gap_policy=DATA_GAP_SKIP_V2).run(
        SyntheticSignals(requests), 'USDRUBF', rows,
        start=date.fromisoformat(config['start']),
        end_exclusive=date.fromisoformat(config['end_exclusive']))
    write_data_quality_reports(output, result, {'USDRUBF':rows}, config, rules)
    csv_write(output/'synthetic_m5.csv', [dict(start=b.start, open=b.open, high=b.high,
        low=b.low, close=b.close, volume=b.volume, problem=b.problem) for b in rows.values()])
    # Explicit independent calendar/tick contract, no hidden source dependency.
    dump(output/'synthetic_contract.json', dict(instrument='USDRUBF', tick='0.01',
        start=config['start'], end_exclusive=config['end_exclusive'],
        windows=[['10:00','14:00'], ['14:05','18:50']], signal_times=requests,
        direction=-1, stop='101.02', target_gross_R='1.5', hold_minutes=60,
        entry_mode=ENTRY_NEXT_OPEN, data_gap_policy=DATA_GAP_SKIP_V2))
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    generate(parser.parse_args().output)
