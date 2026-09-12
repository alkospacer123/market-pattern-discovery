from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Position:
    direction: str
    entry: float
    initial_stop: float
    contracts: int
    remaining_fraction: float = 1.0
    stop: float = field(init=False)
    next_target: int = 0
    realized_r: float = 0.0
    closed: bool = False

    def __post_init__(self):
        self.stop = self.initial_stop

    @property
    def risk(self) -> float:
        return abs(self.entry - self.initial_stop)

    def target_price(self, multiple: float) -> float:
        return self.entry + self.risk * multiple * (1 if self.direction == "LONG" else -1)


class BaselineExitManager:
    def __init__(self, levels=(1.0, 2.0, 3.0), fractions=(0.5, 0.3, 0.2), policy="STOP_FIRST"):
        if len(levels) != len(fractions) or abs(sum(fractions) - 1) > 1e-9:
            raise ValueError("Exit levels/fractions must align and fractions sum to one")
        self.levels, self.fractions, self.policy = tuple(levels), tuple(fractions), policy

    def process(self, position: Position, high: float, low: float) -> list[dict]:
        events: list[dict] = []
        stop_hit = low <= position.stop if position.direction == "LONG" else high >= position.stop
        target = position.target_price(self.levels[position.next_target]) if position.next_target < len(self.levels) else None
        target_hit = target is not None and (high >= target if position.direction == "LONG" else low <= target)
        if stop_hit and target_hit and self.policy == "STOP_FIRST":
            target_hit = False
        if stop_hit:
            signed = (position.stop - position.entry) / position.risk * (1 if position.direction == "LONG" else -1)
            position.realized_r += position.remaining_fraction * signed
            events.append({"event": "STOP", "price": position.stop, "fraction": position.remaining_fraction})
            position.remaining_fraction, position.closed = 0.0, True
            return events
        while target_hit and not position.closed:
            i, multiple = position.next_target, self.levels[position.next_target]
            fraction = min(self.fractions[i], position.remaining_fraction)
            position.realized_r += fraction * multiple
            position.remaining_fraction -= fraction
            events.append({"event": f"TP{i + 1}", "price": position.target_price(multiple), "fraction": fraction})
            position.next_target += 1
            if position.next_target == 1:
                position.stop = position.entry
            elif position.next_target == 2:
                position.stop = position.target_price(1.0)
            if position.next_target == len(self.levels):
                position.closed, position.remaining_fraction = True, 0.0
                break
            target = position.target_price(self.levels[position.next_target])
            target_hit = high >= target if position.direction == "LONG" else low <= target
        return events
