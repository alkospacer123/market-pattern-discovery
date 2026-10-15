"""Pure deterministic fixtures. No I/O, credentials, threads or engine imports."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from math import sin
from ..models import (
    Candle, DataProvenance, ExecutionState, InstrumentStatus, OrderEvent,
    PortfolioSnapshot, PositionSnapshot, RiskSnapshot, RobotId, RobotSnapshot,
    RobotStatus, SignalEvent, State, SystemAlert, Trade, aware,
)

SCENARIOS = {
    "BASELINE": "Исходное состояние: HALTED / NOT_DEPLOYED",
    "HEALTHY": "HEALTHY — исправная тестовая телеметрия",
    "STALE": "STALE — снимок не обновляется",
    "DATA_GAP": "DATA_GAP — пропущена свеча",
    "API_ERROR": "API_ERROR — имитация ошибки API",
    "OPEN_POSITION": "Открытая DEMO-позиция",
    "UNRESOLVED": "UNRESOLVED — исполнение неизвестно",
    "UNAVAILABLE": "Источник недоступен",
    "UNKNOWN": "UNKNOWN — отсутствуют поля",
    "MALFORMED": "Повреждённый синтетический снимок",
}
N4 = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
M15_DEMO = ("DEMO-M15-A", "DEMO-M15-B")  # not approved production instruments
EVENT_TYPES = {
    "BAR": "Получена свеча", "SIGNAL": "Рассчитан сигнал",
    "CONDITION": "Проверены условия", "RISK": "Проверен риск",
    "INTENT": "Сформировано намерение заявки", "ACK": "Получен ответ брокера (имитация)",
    "POSITION": "Наблюдалась позиция", "STOP": "Проверен стоп (имитация)",
    "CLOSE": "Сделка закрыта (DEMO)", "ERROR": "Возникла ошибка",
}


def empty_snapshot(robot_id: RobotId, now: datetime, reason: str) -> RobotSnapshot:
    p = DataProvenance(robot_id, f"DEMO-{robot_id}", "SYNTHETIC/unavailable", None, now)
    status = RobotStatus(p, State.HALTED if robot_id == RobotId.H1 else State.NOT_DEPLOYED,
                         "TradingSystemLab" if robot_id == RobotId.H1 else "IntradayLab",
                         "T3/H1/TRAIL1" if robot_id == RobotId.H1 else "T3/M15/SESSION",
                         "TRAIL1__N4_01__FULL__R15" if robot_id == RobotId.H1 else None,
                         None, None, None, False, None, None, None)
    return RobotSnapshot(status, (), (), (), (), None,
                         RiskSnapshot(p, None, None, None, None, reason),
                         PortfolioSnapshot(p, None, None, None, None, None, None), None,
                         (SystemAlert(p, None, now, "ERROR", "ERROR", reason),))


class SyntheticProvider:
    def snapshot(self, robot_id: RobotId, scenario: str, now: datetime) -> RobotSnapshot:
        aware(now)
        if not isinstance(robot_id, RobotId) or scenario not in SCENARIOS:
            raise ValueError("INVALID_FIXTURE_REQUEST")
        if scenario == "MALFORMED":
            raise ValueError("SYNTHETIC_CORRUPTED_SNAPSHOT")
        if scenario in ("UNAVAILABLE", "UNKNOWN"):
            return empty_snapshot(robot_id, now, "SYNTHETIC: SOURCE_UNAVAILABLE" if scenario == "UNAVAILABLE" else "SYNTHETIC: MISSING_FIELDS")
        tick = datetime.fromtimestamp(int(now.timestamp()) // 2 * 2, timezone.utc)
        observed = tick if scenario != "STALE" else tick.replace(hour=0, minute=0, second=0) - timedelta(minutes=5)
        p = DataProvenance(robot_id, f"DEMO-{robot_id}", f"SYNTHETIC/{robot_id}/{scenario}", observed, now)
        h1 = robot_id == RobotId.H1
        symbols = N4 if h1 else M15_DEMO
        step = timedelta(hours=1) if h1 else timedelta(minutes=15)
        close = observed.replace(minute=0 if h1 else observed.minute // 15 * 15, second=0, microsecond=0)
        state = State.HALTED
        if h1:
            state = {"HEALTHY": State.HEALTHY, "DATA_GAP": State.DATA_GAP,
                     "API_ERROR": State.API_ERROR, "UNRESOLVED": State.UNRESOLVED}.get(scenario, State.HALTED)
        else:
            state = State.NOT_DEPLOYED
        candles, instruments, signals = [], [], []
        for index, symbol in enumerate(symbols):
            base = (100, 12, 9000, 3000)[index] if h1 else (200, 400)[index]
            for n in range(72):
                if scenario == "DATA_GAP" and n == 70:
                    continue
                at = close - step * (71-n)
                open_ = base * (1 + 0.0007*n + 0.005*sin(n/4 + index))
                price = open_ + base * 0.002*sin(n + 0.7)
                candles.append(Candle(p, symbol, at, round(open_, 4), round(max(open_, price)+base*.002, 4),
                                      round(min(open_, price)-base*.002, 4), round(price, 4),
                                      round(base*(1 + .0007*n), 4)))
            instruments.append(InstrumentStatus(p, symbol, State.DATA_GAP if scenario == "DATA_GAP" else state,
                                                close if h1 else None,
                                                "DEMO: условие тренда выполнено; новые входы запрещены" if h1 else "DEMO: сессионное условие; производственная спецификация UNKNOWN",
                                                None, None))
            sample = [c for c in candles if c.instrument == symbol]
            for n, direction in ((16, "LONG"), (42, "EXIT"), (71, "NO SIGNAL")):
                bar = sample[min(n, len(sample)-1)]
                signals.append(SignalEvent(p, symbol, bar.close_at, direction,
                                           "SYNTHETIC: иллюстрация, не расчёт стратегии" if direction != "NO SIGNAL" else "SYNTHETIC: HALTED / NO_RUNTIME_AUTHORITY",
                                           bar.close if direction != "NO SIGNAL" else None))
        positions = () if h1 else None
        if h1 and scenario == "OPEN_POSITION":
            positions = (PositionSnapshot(p, symbols[0], 2, 103.0, 240.0, 101.0, "SYNTHETIC_STOP_PROOF"),)
            instruments[0] = replace(instruments[0], stop_price=101.0, stop_evidence="SYNTHETIC_STOP_PROOF")
        orders = ()
        if h1:
            orders = tuple(OrderEvent(p, symbols[0], observed-timedelta(seconds=20-i), f"DEMO-order-{i}", execution, 2,
                                      2 if execution == ExecutionState.FILL_CONFIRMED else None,
                                      103.0 if execution == ExecutionState.FILL_CONFIRMED else None,
                                      "SYNTHETIC_FILL_PROOF" if execution == ExecutionState.FILL_CONFIRMED else None)
                           for i, execution in enumerate(ExecutionState))
        trades = None
        portfolio = PortfolioSnapshot(p, None, None, None, None, None, None)
        risk = RiskSnapshot(p, None, None, None, None, "NO_RUNTIME_AUTHORITY")
        if h1:
            net = (800., -400., 600., -200., 900.)
            trades = tuple(Trade(p, symbols[i % 4], observed-timedelta(days=65-i*12, hours=4),
                                 observed-timedelta(days=65-i*12), 100.+i, 101.+i, pnl, 10.) for i, pnl in enumerate(net))
            balance, peak, dd = 100000., 100000., 0.
            for pnl in net:
                balance += pnl
                peak = max(peak, balance)
                dd = max(dd, (peak-balance)/peak*100)
            floating = sum(position.unrealized_pnl for position in positions)
            portfolio = PortfolioSnapshot(p, balance+floating, sum(net), floating, 50., 2300/600, dd)
            risk = RiskSnapshot(p, 1.5, 6., 1.2 if positions else 0., 2 if positions else 0,
                                "SYNTHETIC: демонстрация R15, не разрешение")
        status = RobotStatus(p, state, "TradingSystemLab" if h1 else "IntradayLab",
                             "T3/H1/TRAIL1" if h1 else "T3/M15/SESSION",
                             "TRAIL1__N4_01__FULL__R15" if h1 else None,
                             observed if h1 and state == State.HEALTHY else None,
                             close if h1 else None, len(positions) if h1 else None, False,
                             1 if scenario == "API_ERROR" else (0 if h1 else None),
                             "DEMO: Disabled" if h1 else None,
                             "DEMO: пример сессии; runtime отсутствует" if not h1 else None)
        events = tuple(SystemAlert(p, symbols[i % len(symbols)], observed-timedelta(seconds=60-i*3), kind,
                                   "ERROR" if kind == "ERROR" else "INFO", "SYNTHETIC / DEMO: " + text)
                       for i, (kind, text) in enumerate(EVENT_TYPES.items()))
        if scenario != "BASELINE":
            events += (SystemAlert(p, symbols[0], observed, "ERROR" if scenario in ("API_ERROR", "UNRESOLVED", "DATA_GAP", "STALE") else "CONDITION",
                                   "WARNING", f"SYNTHETIC: сценарий {scenario}"),)
        return RobotSnapshot(status, tuple(instruments), tuple(candles), tuple(signals), orders,
                             positions, risk, portfolio, trades, events)


def read_safely(provider, robot_id: RobotId, scenario: str, now: datetime) -> RobotSnapshot:
    """One robot's failure must not reuse its last HEALTHY or affect its neighbour."""
    try:
        value = provider.snapshot(robot_id, scenario, now)
        if not isinstance(value, RobotSnapshot) or value.status.provenance.robot_id != robot_id:
            raise ValueError("WRONG_ROBOT_SNAPSHOT")
        return value
    except Exception:
        # Ordinary provider failures only; KeyboardInterrupt/SystemExit propagate.
        # Never display raw exception payloads: future sources may include secrets.
        return empty_snapshot(robot_id, now, "SYNTHETIC: SNAPSHOT_INVALID_OR_UNAVAILABLE")
