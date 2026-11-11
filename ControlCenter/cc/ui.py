"""Russian, read-only Streamlit views. All inputs are immutable demo snapshots."""
from datetime import datetime
import streamlit as st
from .analytics import monthly
from .charts import candle_chart
from .freshness import MSK, display_state, freshness, metric, stamp
from .models import RobotId, RobotSnapshot, SourceKind, State
from .providers.synthetic import EVENT_TYPES

PAGES = ("Главная", "Журнал", "Управление")
CONTROLS = ("Пауза новых входов", "Аварийная остановка", "Безопасная остановка", "Перезапуск", "Диагностика")
CONTROL_EXPLANATION = "Управление ещё не подключено. Команды START / STOP / RESTART не выполняются."
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
    quality = freshness(p, now)
    if p.source_kind == SourceKind.WINDOWS_OS_ONLY and snapshot.status.state == State.STALE:
        quality = State.STALE  # Preserve latched expiry even after a clock rewind.
    label = 'CURRENT' if p.source_kind == SourceKind.WINDOWS_OS_ONLY and quality == State.HEALTHY else quality
    st.caption(f"Последнее наблюдение источника: {stamp(p.observed_at)} · качество {label}")
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
        st.caption("Выбранная конфигурация M15: T3_M15_T1_TRAIL35_N4_R15 · SESSION T1 / NEXT_OPEN · FULL N4 · R15 1,5% на позицию / 6% общий номинальный риск. Runtime ещё не развёрнут; LIVE-авторизация UNKNOWN.")


def robot_card(snapshot: RobotSnapshot, now: datetime, local_report=None):
    s = snapshot.status
    with st.container(border=True):
        st.subheader(s.strategy)
        local_valid = (local_report is not None and s.provenance.robot_id == RobotId.H1
                       and s.provenance.source_kind == SourceKind.WINDOWS_OS_ONLY)
        fresh = local_valid and local_report["status"] == "CURRENT"
        if fresh:
            st.success("T3/H1/TRAIL1 · HEALTHY по локальному H1 CHECK · ARMED")
            st.caption("Локальная сверка H1 PASS; независимая FINAM-сверка и покрытие стопами НЕ ДОКАЗАНЫ.")
        elif local_valid:
            st.warning("T3/H1/TRAIL1 · H1 CHECK STALE · текущий HEALTHY не подтверждён")
        else:
            status_banner(snapshot, now)
        left, right = st.columns(2)
        if fresh:
            left.metric("Локальные позиции · H1 CHECK", str(local_report["positions"]))
            right.metric("Последние 10 циклов · H1 CHECK",
                         str(sum(c["Результат"] == "PASS" for c in local_report["cycles"])) + "/10 PASS")
        else:
            left.metric(f"Открытые позиции · {mode(snapshot)}", "UNKNOWN" if s.open_positions is None else str(s.open_positions))
            right.metric(f"Ошибки · {mode(snapshot)}", "UNKNOWN" if s.error_count is None else str(s.error_count))
        st.write("**Последняя завершённая свеча:** " + stamp(s.last_bar_at))
        if fresh:
            st.write("**Heartbeat H1 CHECK:** " + stamp(local_report["observed_at"]))
            st.caption("Цикл H1: " + str(local_report["cycle_count"]) + " · Unresolved (локально): " + str(local_report["unresolved"]))
        else:
            st.write("**Heartbeat:** " + stamp(s.heartbeat_at))
        st.write("**Windows Task:** " + (s.task_state or "UNKNOWN"))
        st.write("**Производственная identity:** " + (s.production_identity or "UNKNOWN"))
        source(snapshot, now)


def overview(snapshots: dict, now: datetime, broker=None, local_report=None):
    h1 = snapshots[RobotId.H1]
    local = (local_report if h1.status.provenance.source_kind == SourceKind.WINDOWS_OS_ONLY else None)
    fresh = local is not None and local["status"] == "CURRENT"
    st.subheader("H1 · T3 / TRAIL1")
    if fresh:
        st.success("HEALTHY · ARMED · сверка H1 PASS")
    elif local is not None:
        st.warning("STALE · H1 CHECK устарел")
    else:
        st.warning("UNKNOWN · нет актуального H1 CHECK")
    a, b, c, d = st.columns(4)
    a.metric("Цикл", str(local["cycle_count"]) if fresh else "—")
    b.metric("Позиции H1", str(local["positions"]) if fresh else "—")
    c.metric("Стопы H1", str(local["stops"]) if fresh else "—")
    d.metric("Ошибки / unresolved", str(local["unresolved"]) if fresh else "—")
    if fresh:
        st.caption("Heartbeat " + stamp(local["observed_at"]) + " · Task " + (h1.status.task_state or "UNKNOWN") +
                   " · 10 циклов: " + str(sum(v["Результат"] == "PASS" for v in local["cycles"])) + "/10 PASS")
    else:
        st.caption("Windows Task: " + (h1.status.task_state or "UNKNOWN") + " · последнее достоверное здоровье неизвестно")
    st.divider()
    st.subheader("FINAM · брокер")
    if not broker or broker.get("status") == "UNKNOWN":
        st.info("Нет принятого снимка брокера")
    else:
        if broker["status"] == "STALE":
            st.warning("STALE · брокерский снимок устарел")
        else:
            st.caption("CURRENT · отдельный FINAM READONLY-снимок")
        a, b, c = st.columns(3)
        a.metric("Заявки", str(broker["order_rows"]) if broker["status"] == "CURRENT" else "—")
        b.metric("Активные", str(broker["active_orders"]) if broker["status"] == "CURRENT" else "—")
        c.metric("SLTP", str(broker["active_sltp"]) if broker["status"] == "CURRENT" else "—")
        st.caption("Снимок " + stamp(broker["received_at"]))
    st.divider()
    st.subheader("M15")
    st.caption("Источник M15 не подключён к Control Center")
    with st.expander("Сведения об источниках и N4", expanded=False):
        st.caption("H1 CHECK — локальный отчёт движка; брокерские позиции, исполнения и покрытие стопов он не подтверждает.")
        st.caption("FINAM — отдельное наблюдение; нули не доказывают FLAT без полноты ответа и привязки счёта.")
        if broker and broker.get("status") != "UNKNOWN":
            st.dataframe([{"Инструмент": name, "В ответе FINAM": broker["quantities"][name]}
                          for name in ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")],
                         width="stretch", hide_index=True)
        st.caption("Текущее подтверждение сигналов/причин отказов, PnL и риска — отсутствует.")

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


def broker_readonly_view(broker):
    """Separate FINAM response rows; neither H1 health nor position protection."""
    st.subheader("FINAM · отдельное READONLY-наблюдение брокера")
    if not broker or broker.get('status') == 'UNKNOWN':
        st.info("UNKNOWN · защищённый брокерский снимок ещё не принят. Нажмите «Обновить данные» после отдельной публикации.")
        return
    if broker['status'] == 'STALE':
        st.warning("STALE · данные устарели, показаны только как история наблюдения.")
    else:
        st.caption("CURRENT · принятый обезличенный ответ FINAM REAL_READONLY; только время получения API-ответа.")
    st.caption("Ответ получен: " + stamp(broker['received_at']) +
               ". Оригинальная временная метка брокерского снимка: НЕ ПРЕДОСТАВЛЕНА.")
    st.dataframe([{"Инструмент": symbol, "Контрактов в ответе": broker['quantities'][symbol]}
                  for symbol in ('USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF')],
                 hide_index=True, width="stretch")
    a, b, c = st.columns(3)
    a.metric("Строки заявок FINAM", broker['order_rows'])
    b.metric("Активные заявки FINAM", broker['active_orders'])
    c.metric("Активные SLTP-строки", broker['active_sltp'])
    st.caption("Других инструментов с ненулевым количеством в ответе: " +
               str(broker['other_nonzero']) +
               ". Полнота/пагинация ответа: НЕ ДОКАЗАНА. Нули не означают подтверждённый flat.")
    st.caption("H1 ownership: UNVERIFIED · покрытие стопом: UNVERIFIED · FILL, PnL, equity: UNKNOWN. " 
               "Одна заявка или SLTP не доказывает защиту позиции.")


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


def monitor(snapshot: RobotSnapshot, now: datetime, broker=None, local_report=None):
    fresh = (local_report is not None and local_report["status"] == "CURRENT"
             and snapshot.status.provenance.source_kind == SourceKind.WINDOWS_OS_ONLY)
    if fresh:
        st.success("T3/H1/TRAIL1 · HEALTHY по локальному H1 CHECK · ARMED")
        st.caption("Локальные данные H1; не независимая FINAM-сверка.")
    elif local_report is not None and snapshot.status.provenance.source_kind == SourceKind.WINDOWS_OS_ONLY:
        st.warning("T3/H1/TRAIL1 · H1 CHECK STALE · текущий HEALTHY не подтверждён")
    else:
        status_banner(snapshot, now)
    source(snapshot, now)
    st.write("**Heartbeat H1 CHECK:** " + stamp(local_report["observed_at"]) if fresh else "**Heartbeat:** " + stamp(snapshot.status.heartbeat_at))
    st.write("**Последняя завершённая свеча:** " + stamp(snapshot.status.last_bar_at))
    if snapshot.status.session:
        st.info(snapshot.status.session)
    chart_view(snapshot, snapshot.status.provenance.robot_id.value)
    readonly_details(snapshot)
    if broker is not None:
        broker_readonly_view(broker)
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


def trades_view(snapshot: RobotSnapshot, now: datetime, broker=None):
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
    if broker is not None:
        broker_readonly_view(broker)
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


def events_view(snapshots: dict, now: datetime, local_report=None):
    st.subheader("Последние 10 циклов H1")
    if local_report is None:
        st.info("Нет опубликованного H1 CHECK. Обнови данные на главной странице.")
        return
    if local_report["status"] == "STALE":
        st.warning("STALE · показана история, не текущее состояние")
    st.dataframe(local_report["cycles"], hide_index=True, width="stretch")
    st.caption("Локальный журнал H1 · время heartbeat: " + stamp(local_report["observed_at"]))
    st.caption("Отдельные сигналы T3 и причины SKIP этот источник не публикует.")


def controls_view(snapshots: dict, now: datetime):
    st.subheader("Управление роботами")
    st.info(CONTROL_EXPLANATION)
    st.caption("H1 · управление недоступно")
    st.caption("M15 · управление недоступно")
    st.caption("Никаких торговых действий из панели не выполняется.")


def render(page: str, snapshots: dict, now: datetime, broker=None, local_report=None):
    if page == PAGES[0]:
        overview(snapshots, now, broker=broker, local_report=local_report)
    elif page == PAGES[1]:
        events_view(snapshots, now, local_report=local_report)
    else:
        controls_view(snapshots, now)
