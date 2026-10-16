"""Russian, read-only Streamlit views. All inputs are immutable demo snapshots."""
from datetime import datetime
import streamlit as st
from .analytics import monthly
from .charts import candle_chart
from .freshness import MSK, display_state, freshness, metric, stamp
from .models import RobotId, RobotSnapshot, SourceKind, State
from .providers.synthetic import EVENT_TYPES

PAGES = ("Главная панель", "Монитор H1", "Монитор M15", "Графики и сигналы",
         "Сделки и статистика", "Журнал событий", "Управление")
CONTROLS = ("Пауза новых входов", "Аварийная остановка", "Безопасная остановка", "Перезапуск", "Диагностика")
CONTROL_EXPLANATION = "Управление будет доступно после отдельной разработки, проверки безопасности и разрешения оператора"
CSS = """
<style>
.block-container {max-width:1450px;padding-top:4rem;padding-bottom:3rem;}
[data-testid="stMetricValue"] {font-size:1.65rem;}
[data-testid="stMetricLabel"] {color:#9eafc4;}
[data-testid="stSidebar"] {border-right:1px solid #253046;}
h1 {letter-spacing:-.035em;} h3 {letter-spacing:-.02em;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
@media(max-width:640px) {.block-container {padding:4rem 1rem 1rem;} h1 {font-size:1.8rem;}
[data-testid="stMetricValue"] {font-size:1.35rem;}}
</style>
"""


def mode(snapshot):
    return "SYNTHETIC / DEMO" if snapshot.status.provenance.source_kind == SourceKind.SYNTHETIC else snapshot.status.provenance.source_kind.value


def source(snapshot: RobotSnapshot, now: datetime):
    p = snapshot.status.provenance
    st.caption(f"{mode(snapshot)} · {p.account_scope} · {p.source}")
    st.caption(f"Последнее наблюдение источника: {stamp(p.observed_at)} · качество {freshness(p, now)}")
    st.caption(f"Прочитано интерфейсом: {stamp(p.received_at)}. Время получения не подменяет время источника.")


def status_banner(snapshot: RobotSnapshot, now: datetime):
    status = snapshot.status
    state = display_state(status, now)
    text = f"{status.strategy} · {state} · {mode(snapshot)}"
    if state == State.HEALTHY:
        st.success(text)
    elif state in (State.HALTED, State.NOT_DEPLOYED):
        st.info(text)
    else:
        st.warning(text)
    st.caption(f"Заявленное состояние: {status.state}. Торговые действия панели: ЗАПРЕЩЕНЫ. Фактическая trading authorization: UNKNOWN. Аккаунт: {status.provenance.account_scope}.")
    if status.provenance.robot_id == RobotId.M15:
        st.caption("NO_RUNTIME_AUTHORITY · production identity и фактический риск UNKNOWN. График — отдельный DEMO-пример.")
        st.caption("Документированный план #527: T3_M15_T1_TRAIL35_N4_R20 · SESSION T1 / NEXT_OPEN · FULL N4 · R20 2% / 8%. Это план будущего робота, без LIVE-авторизации.")


def robot_card(snapshot: RobotSnapshot, now: datetime):
    s = snapshot.status
    with st.container(border=True):
        st.subheader(s.strategy)
        status_banner(snapshot, now)
        left, right = st.columns(2)
        left.metric(f"Открытые позиции · {mode(snapshot)}", "UNKNOWN" if s.open_positions is None else str(s.open_positions))
        right.metric(f"Ошибки · {mode(snapshot)}", "UNKNOWN" if s.error_count is None else str(s.error_count))
        st.write("**Последняя завершённая свеча:** " + stamp(s.last_bar_at))
        st.write("**Heartbeat:** " + stamp(s.heartbeat_at))
        st.write("**Windows Task:** " + (s.task_state or "UNKNOWN"))
        st.write("**Производственная identity:** " + (s.production_identity or "UNKNOWN"))
        source(snapshot, now)


def overview(snapshots: dict, now: datetime):
    st.subheader("Два робота · два независимых контура")
    st.caption("H1 отображает только состояние своего выбранного источника; M15 — NOT_DEPLOYED. Сценарии в боковой панели меняют только локальные тестовые снимки.")
    for column, robot_id in zip(st.columns(2), RobotId):
        with column:
            robot_card(snapshots[robot_id], now)
    st.info("Счета, капитал и риск H1 / M15 отображаются раздельно. Суммарного портфеля двух роботов нет.")


def chart_view(snapshot: RobotSnapshot, key: str):
    symbols = [row.instrument for row in snapshot.instruments]
    if not symbols:
        st.warning("UNKNOWN — источник данных недоступен; свечи и сигналы не восстановлены из старого снимка.")
        return
    a, b = st.columns([2, 1])
    symbol = a.selectbox(f"Инструмент · {mode(snapshot)}", symbols, key=f"symbol-{key}")
    count = b.selectbox("Период: число свечей", [24, 48, 72], index=2, key=f"period-{key}")
    if snapshot.candles:
        st.plotly_chart(candle_chart(snapshot, symbol, count), use_container_width=True, key=f"chart-{key}")
    else:
        st.info("UNKNOWN / STALE — пригодных свечей для графика нет.")
    rows = [dict(Время=stamp(row.occurred_at), Инструмент=row.instrument, Сигнал=row.direction,
                 Причина=row.reason or "UNKNOWN", Источник=row.provenance.source)
            for row in snapshot.signals if row.instrument == symbol]
    st.dataframe(rows, width="stretch", hide_index=True)
    if snapshot.status.provenance.source_kind == SourceKind.SYNTHETIC:
        st.caption("Свечи, отметки входа/выхода и DEMO-линия созданы формулой; индикаторы T3 и торговые решения не вычисляются.")
    else:
        st.caption(f"{mode(snapshot)}: только опубликованные завершённые свечи и события. UNKNOWN / Причина не опубликована. Актуальность H1 без утверждённого календаря UNKNOWN. T3 не пересчитывается.")


def order_rows(snapshot: RobotSnapshot):
    return [{"Время": stamp(o.occurred_at), ("Заявка DEMO" if mode(snapshot) == "SYNTHETIC / DEMO" else ("Заявка fixture" if mode(snapshot) == "OFFLINE_FIXTURE" else "Заявка источника")): o.order_id, "Инструмент": o.instrument,
             "Состояние": o.state.value, "Запрошено": str(o.quantity) if o.quantity is not None else "UNKNOWN",
             "Исполнено": str(o.filled_quantity) if o.filled_quantity is not None else "UNKNOWN",
             "Цена исполнения": metric(o.fill_price), "Доказательство": o.fill_evidence or "UNKNOWN"}
            for o in snapshot.orders]


def readonly_details(snapshot):
    if snapshot.windows_observations:
        st.caption('Windows OS READONLY: TASK_RUNNING / PROCESS_OBSERVED не доказывают ROBOT_HEALTHY, BROKER_CONNECTED или TRADING_AUTHORIZED. Отсутствие процесса не доказывает отсутствие позиций.')
        st.dataframe([{"Наблюдение": r.name, "Источник": r.source, "Факт": r.state,
                       "Наблюдалось": stamp(r.observed_at), "Актуальность": r.freshness,
                       "Authority": r.authority, "Причина": r.reason, "Metadata / identity": r.value or 'UNKNOWN'}
                      for r in snapshot.windows_observations], hide_index=True, use_container_width=True)
        st.caption('Heartbeat, сигналы, позиции, ордера, FILL, ACTIVE SLTP, финансы, PnL, депозиты и просадки: UNKNOWN. Metadata source DISABLED: native noninterference не пройден.')
    if snapshot.readonly_identity is not None:
        st.caption(snapshot.readonly_identity)
    if snapshot.readonly_observations:
        st.dataframe([{"Набор / источник": row.name, "Время наблюдения": stamp(row.observed_at),
                       "Актуальность": row.state.value} for row in snapshot.readonly_observations],
                     hide_index=True, use_container_width=True)
    details = snapshot.h1_readonly
    if details is None:
        return
    st.caption(f"OFFLINE_FIXTURE · spec {details.production_specification_id} · accepted code {details.accepted_code_commit}")
    st.caption(f"Сформирован: {stamp(details.generated_at)} · Последний успешный цикл: {stamp(details.last_successful_cycle_at)}")
    st.caption(f"Reconciliation: {details.reconciliation} · unresolved: {details.unresolved_intents if details.unresolved_intents is not None else 'UNKNOWN'} · источник: {details.source_status}")
    st.caption(f"Полнота заявок: {details.orders_complete}; полнота позиций: {details.positions_complete}. Отсутствие строк не доказывает ноль.")
    st.dataframe([{"Группа": row.name, "Наблюдение": stamp(row.observed_at), "Актуальность": row.state.value}
                  for row in details.observations], hide_index=True, width="stretch")
    st.dataframe([{"Инструмент": row.instrument, "Закрытие H1 (CLOSE)": stamp(row.close_at),
                   "Источник времени": row.time_source, "Пробелы": str(row.gaps) if row.gaps is not None else "UNKNOWN",
                   "Качество": row.quality, "Актуальность": row.freshness.value} for row in details.bars],
                 hide_index=True, width="stretch")
    st.dataframe([{"Инструмент": row.instrument, "Сторона": row.side, "Контракты": row.quantity,
                   "Ожидаемое защитное количество": row.expected_quantity,
                   "Наблюдаемое защитное количество": row.observed_quantity,
                   "Статус поручения": row.broker_status, "Проверено": stamp(row.checked_at),
                   "Evidence": row.evidence or "UNKNOWN",
                   "Покрытие в тестовом снимке": "FIXTURE_CONFIRMED" if row.protected else "UNKNOWN"}
                  for row in details.stops], hide_index=True, width="stretch")
    st.caption(f"Вводы: {metric(details.deposits)} · Выводы: {metric(details.withdrawals)} · Доступная маржа: {metric(details.available_margin)}")


def monitor(snapshot: RobotSnapshot, now: datetime):
    status_banner(snapshot, now)
    source(snapshot, now)
    st.write("**Heartbeat:** " + stamp(snapshot.status.heartbeat_at))
    st.write("**Последняя завершённая свеча:** " + stamp(snapshot.status.last_bar_at))
    if snapshot.status.session:
        st.info(snapshot.status.session)
    chart_view(snapshot, snapshot.status.provenance.robot_id.value)
    readonly_details(snapshot)
    st.subheader(f"Условия, стопы и состояние инструментов · {mode(snapshot)}")
    st.dataframe([{"Инструмент": r.instrument, "Состояние источника": r.state.value,
                   "Свеча runtime": stamp(r.last_bar_at), "Условие / отказ": r.condition or "UNKNOWN",
                   "Стоп": metric(r.stop_price), "Доказательство стопа": r.stop_evidence or "UNKNOWN"}
                  for r in snapshot.instruments], width="stretch", hide_index=True)
    risk = snapshot.risk
    st.subheader(f"Риск отдельного счёта · {mode(snapshot)}")
    cols = st.columns(4)
    for col, label, value in zip(cols, ("На позицию", "Максимум", "Использовано", "Контрактов"),
                                 (risk.per_position_pct, risk.maximum_total_pct, risk.used_pct, risk.contracts)):
        col.metric(label, metric(value, " %" if label != "Контрактов" else ""))
    st.caption(risk.reason or "UNKNOWN")
    st.subheader(f"Состояния заявок · {mode(snapshot)}")
    st.caption("INTENT → REQUESTED → ACK не доказывают исполнение. POSITION_OBSERVED не доказывает fill. Только FILL_CONFIRMED имеет отдельное доказательство; UNRESOLVED требует проверки.")
    if snapshot.orders:
        st.dataframe(order_rows(snapshot), width="stretch", hide_index=True)
    else:
        st.info("UNKNOWN — журнал заявок runtime не подключён.")


def choose_robot(snapshots: dict, key: str) -> RobotSnapshot:
    robot = st.selectbox("Независимый робот / счёт", list(RobotId), key=key,
                         format_func=lambda value: f"{value} · {snapshots[value].status.provenance.account_scope}")
    return snapshots[robot]


def trades_view(snapshot: RobotSnapshot, now: datetime):
    status_banner(snapshot, now)
    source(snapshot, now)
    st.subheader(f"Финансы отдельного счёта · {mode(snapshot)}")
    p = snapshot.portfolio
    items = (("Капитал", p.equity, " ₽"), ("Реализованный Net PnL", p.realized_pnl, " ₽"),
             ("Нереализованный PnL", p.unrealized_pnl, " ₽"), ("Комиссии", p.commissions, " ₽"),
             ("Profit Factor (net)", p.profit_factor, ""), ("Максимальная просадка", p.maximum_drawdown_pct, " %"))
    for start in (0, 3):
        for col, (label, value, suffix) in zip(st.columns(3), items[start:start+3]):
            col.metric(label, metric(value, suffix))
    if snapshot.status.provenance.source_kind == SourceKind.SYNTHETIC:
        st.caption("DEMO: начальный капитал H1 100 000 ₽; Net PnL уже учитывает комиссии. Просадка и PF по закрытым DEMO-сделкам; вводы/выводы отсутствуют. M15: финансовая authority отсутствует.")
    else:
        st.caption(f"{mode(snapshot)}. Equity не является чистой торговой прибылью. Неполные финансы скрыты; PnL по ACK/модельным ценам не вычисляется.")
        readonly_details(snapshot)
    st.subheader(f"Активные позиции · {mode(snapshot)}")
    if snapshot.positions is None:
        st.info("UNKNOWN — позиции не наблюдались.")
    elif not snapshot.positions:
        st.caption(f"{mode(snapshot)}: полное наблюдение позиций сообщает 0.")
    else:
        st.dataframe([{"Инструмент": r.instrument, "Контрактов": r.quantity, "Сторона": r.side or "UNKNOWN", "Подтверждённая цена входа": metric(r.entry_price),
                       "PnL, ₽": metric(r.unrealized_pnl), "Стоп": metric(r.stop_price),
                       "Доказательство стопа": r.stop_evidence or "UNKNOWN"} for r in snapshot.positions],
                     width="stretch", hide_index=True)
    st.subheader(f"История сделок · {mode(snapshot)}")
    if snapshot.trades is None:
        st.info("UNKNOWN — журнал сделок runtime не подключён.")
    else:
        st.dataframe([{"Инструмент": r.instrument, "Вход": stamp(r.entry_at), "Выход": stamp(r.exit_at),
                       "Цена входа DEMO": r.entry_price, "Цена выхода DEMO": r.exit_price,
                       "Net PnL DEMO, ₽": r.net_pnl, "Комиссия DEMO, ₽": r.commission} for r in snapshot.trades],
                     width="stretch", hide_index=True)
        st.subheader("Месячная статистика · DEMO")
        st.dataframe(monthly(snapshot.trades), width="stretch", hide_index=True)


def events_view(snapshots: dict, now: datetime):
    st.subheader("Хронология событий · источник указан в каждой записи")
    a, b = st.columns(2)
    robots = a.multiselect("Роботы", list(RobotId), default=list(RobotId))
    kinds = b.multiselect("Типы событий", list(EVENT_TYPES), format_func=lambda v: EVENT_TYPES[v])
    all_events = [e for snapshot in snapshots.values() for e in snapshot.events]
    symbols = sorted({e.instrument for e in all_events if e.instrument})
    c, d = st.columns(2)
    instruments = c.multiselect("Инструменты", symbols)
    query = d.text_input("Поиск по сообщению")
    start, end = st.columns(2)
    since = start.date_input("С даты (MSK)", now.astimezone(MSK).date())
    until = end.date_input("По дату (MSK)", now.astimezone(MSK).date())
    if since > until:
        st.warning("Начальная дата позже конечной.")
        return
    rows = [e for e in all_events if e.provenance.robot_id in robots
            and (not kinds or e.kind in kinds) and (not instruments or e.instrument in instruments)
            and since <= e.occurred_at.astimezone(MSK).date() <= until and query.casefold() in e.message.casefold()]
    st.caption(f"Найдено событий: {len(rows)}. История ограничена текущими снимками; отсутствие событий не доказывает отсутствие операций.")
    st.dataframe([{"Время UTC / MSK": stamp(e.occurred_at), "Робот": e.provenance.robot_id.value,
                   "Счёт DEMO": e.provenance.account_scope, "Инструмент": e.instrument or "UNKNOWN",
                   "Тип": EVENT_TYPES.get(e.kind, e.kind), "Уровень": e.severity,
                   "Событие DEMO": e.message, "Источник": e.provenance.source,
                   "Время источника": stamp(e.provenance.observed_at), "Режим": e.provenance.source_kind.value}
                  for e in sorted(rows, key=lambda row: row.occurred_at, reverse=True)], width="stretch", hide_index=True)


def controls_view(snapshots: dict, now: datetime):
    st.subheader("Управление · недоступно в CC-02")
    st.warning(CONTROL_EXPLANATION)
    for robot_id in RobotId:
        with st.container(border=True):
            st.write(f"**{robot_id} · {snapshots[robot_id].status.provenance.account_scope}**")
            status_banner(snapshots[robot_id], now)
            for label in CONTROLS:
                st.button(label, key=f"disabled-{robot_id}-{label}", disabled=True, width="stretch")
    st.caption("Кнопки не имеют обработчиков. Отдельный защищённый control plane — будущая работа после проверки и разрешения оператора.")


def render(page: str, snapshots: dict, now: datetime):
    if page == PAGES[0]:
        overview(snapshots, now)
    elif page in (PAGES[1], PAGES[2]):
        monitor(snapshots[RobotId.H1 if page == PAGES[1] else RobotId.M15], now)
    elif page == PAGES[3]:
        snapshot = choose_robot(snapshots, "chart-robot")
        status_banner(snapshot, now)
        source(snapshot, now)
        chart_view(snapshot, "signals")
    elif page == PAGES[4]:
        trades_view(choose_robot(snapshots, "trades-robot"), now)
    elif page == PAGES[5]:
        events_view(snapshots, now)
    else:
        controls_view(snapshots, now)
