"""Declared research windows and dated tick grids, independent of strategy."""
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo


class MarketRules:
    def __init__(self, config):
        self.zone = ZoneInfo(config['timezone'])
        self.calendar = config['calendar']
        self.schedule = {
            symbol: [(datetime.fromisoformat(at).replace(tzinfo=self.zone), Decimal(step))
                     for at, step in items]
            for symbol, items in config['tick_schedule'].items()
        }
        for items in self.schedule.values():
            if items != sorted(items) or any(step <= 0 for _, step in items):
                raise ValueError('INVALID_TICK_SCHEDULE')

    def at(self, day, clock):
        return datetime.fromisoformat(f'{day} {clock}:00').replace(tzinfo=self.zone)

    def windows(self, day):
        if day.weekday() >= 5 or day.strftime('%m-%d') in self.calendar['holidays']:
            return []
        items = [list(w) for w in self.calendar['windows']]
        extension = self.calendar.get('extended_lunch')
        if extension and date.fromisoformat(extension['start']) <= day < date.fromisoformat(extension['end_exclusive']):
            items[1][0] = extension['pm_start']
        return [(self.at(day, a), self.at(day, z)) for a, z in items]

    def tick(self, symbol, at):
        found = [step for first, step in self.schedule[symbol] if first <= at]
        if not found:
            raise ValueError('NO_HISTORICAL_TICK')
        return found[-1]
