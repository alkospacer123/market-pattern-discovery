"""V20 operator-only Streamlit entrypoint. The legacy Intel app.py is unchanged."""
from datetime import datetime, timedelta, timezone
import streamlit as st
from cc.manual_gate import export_gate
from cc.v20_contract import ROBOTS, LABELS, unconnected, age, heartbeat_health
from cc.v20_receiver import acquire
from cc.v20_staging import acquire_staging
from cc.v20_manual_export import refresh_once
from v20_admin_control import admin_ready, confirmation, submit

MSK = timezone(timedelta(hours=3))
PAGES = ("Главная", "Журнал", "Управление")

st.set_page_config(page_title="V20 · Control Center", page_icon="◈", layout="wide",
                   initial_sidebar_state="collapsed")
header, actions = st.columns([5, 1], vertical_alignment="center")
with header:
    st.title("V20 · Control Center")
    st.caption("Shallow · OBV · Inside | один проект, три независимых робота")
with actions:
    refresh = st.button("Обновить данные", key="v20-manual-refresh",
                        use_container_width=True)
    last_check_view = st.empty()
tabs = st.tabs(PAGES)


def show_time(at):
    return at.astimezone(MSK).strftime("%d.%m.%Y %H:%M:%S МСК") if at else "—"


def healthy_label(report):
    status = report["status"]
    return {"HEALTHY": "HEALTHY", "HALTED": "HALTED", "FAULT": "FAULT",
            "UNKNOWN": "UNKNOWN", "STALE": "STALE",
            "NOT_CONNECTED": "НЕ ПОДКЛЮЧЁН", "STAGING": "STAGING · LIVE OFF"}.get(status, "UNKNOWN")


def overview(snapshots, now):
    """Only operator health signals. Trading details belong in FINAM."""
    for robot in ROBOTS:
        report = snapshots[robot]
        status = report["status"]
        current = status in ("HEALTHY", "HALTED", "FAULT")
        with st.container(border=True):
            left, right = st.columns([2, 3])
            with left:
                st.subheader(LABELS[robot])
                if status == "HEALTHY":
                    st.success(healthy_label(report))
                elif status == "FAULT":
                    st.error(healthy_label(report))
                elif status in ("STALE", "HALTED"):
                    st.warning(healthy_label(report))
                else:
                    st.info(healthy_label(report))
            with right:
                pulse = heartbeat_health(report, now)
                st.markdown("**Heartbeat:** " + {
                    "HEALTHY": "🟢 HEALTHY",
                    "STALE": "🔴 UNHEALTHY",
                    "UNKNOWN": "⚪ НЕТ ДАННЫХ",
                }[pulse])
                if status == "STAGING":
                    st.markdown("**Windows Task:** DISABLED · **Kill switch:** НЕТ ДАННЫХ")
                elif current:
                    st.markdown("**Windows Task:** " + report["task_state"] +
                                " · **Kill switch:** " + report["kill_switch"])
                    error_code = report["last_error_code"]
                    if error_code not in ("NONE", "UNKNOWN"):
                        st.caption("Последняя ошибка: " + error_code)
                elif status == "STALE":
                    st.caption("Текущее состояние Task/защиты и ошибок не подтверждено")
                else:
                    if report.get("reason") == "OPERATOR_SID_MISMATCH":
                        st.caption("Проверка отклонена: SID панели не совпадает с владельцем V20 Task")
                    else:
                        st.caption("Состояние Windows Task и ошибок не подтверждено")
    with st.expander("Об источниках", expanded=False):
        st.caption("CC-04: по ручному запросу используются подтверждённые V20 READONLY-снимки или штатные operator-check V20-07. Проверки не запускают торговлю.")
        st.caption("STAGING · LIVE OFF означает лишь проверенную отключённую Windows Task и блокирующее действие на момент запроса. Не означает работоспособный runtime.")
        st.caption("HEALTHY означает состояние по локальному отчёту; не подтверждает сделки, брокерские позиции и SLTP FINAM.")
        st.caption("Heartbeat: HEALTHY — свежий сигнал; UNHEALTHY — сигнал просрочен более чем на 5 минут; НЕТ ДАННЫХ — источник или подтверждённый heartbeat отсутствует.")
        st.caption("Heartbeat HEALTHY означает только свежий сигнал, а не разрешение торговли и не исправность всех компонентов.")
        st.caption("Дата рядом с кнопкой — время последней ручной проверки панелью, не обновления данных самого робота.")
        st.caption("Обновление только вручную; выполняется лишь READONLY-проверка. Торговые и управляющие команды недоступны.")


def journal(snapshots):
    st.subheader("Последние циклы и диагностика")
    for robot in ROBOTS:
        report = snapshots[robot]
        with st.expander(LABELS[robot] + " · " + healthy_label(report), expanded=False):
            if report.get("reason") == "LOCAL_REPORT":
                st.caption("Источник V20 LIVE: реальные проходы live-m15.jsonl; не журнал сделок FINAM.")
            if report["events"]:
                # Show newest first; the source contract accepts up to ten worker attempts.
                recent = tuple(reversed(report["events"][-10:]))
                st.dataframe([{"Время": show_time(event["at"]),
                               "Цикл": event["cycle"], "Результат": event["result"],
                               "Причина": event["code"]} for event in recent],
                             hide_index=True, width="stretch")
            else:
                st.caption("Подтверждённых событий пока нет")
            if report["status"] == "STALE":
                st.caption("Исторические события · снимок STALE")
            if report["status"] == "STAGING":
                workers = "0" if report.get("workers_observed") == 0 else "НЕТ ДАННЫХ"
                st.caption("Staging: LIVE OFF · Worker: " + workers + " · Исполнение заблокировано")
                st.caption("Reconciliation: НЕТ ДАННЫХ · Последняя ошибка: НЕТ ДАННЫХ")


def controls():
    """Explicitly confirmed actions through installed pinned CC-07 executor."""
    st.subheader("Управление")
    connected = st.session_state.get("cc07-admin-ready") is True
    if not connected:
        st.info("Административный оператор пока не подтверждён. Нажмите «Обновить данные» для проверки.")
        typed = ""
    else:
        st.warning("ВНИМАНИЕ: кнопки исполняют реальные команды с правами администратора. START/RESTART включают ARM; STOP требует FINAM FLAT; PAUSE запрещает новые входы. Для каждой команды нужно точное подтверждение.")
        typed = st.text_input(
            "Для подтверждения введите: cc07 действие имя-робота",
            value="", key="cc07-action-confirm",
            placeholder="cc07 pause v20-shallow",
        )
    for robot in ROBOTS:
        st.markdown("**" + LABELS[robot] + "**")
        columns = st.columns(4)
        local_id = robot.lower().replace("_", "-")
        for column, action in zip(columns, ("START", "PAUSE", "STOP", "RESTART")):
            name = action.lower()
            phrase = confirmation(local_id, name)
            with column:
                clicked = st.button(
                    action, key="cc07-" + robot.lower() + "-" + name,
                    disabled=not (connected and typed == phrase),
                    use_container_width=True,
                )
                if clicked:
                    answer = submit(local_id, name, typed)
                    st.session_state["cc07-last-response"] = answer
    answer = st.session_state.get("cc07-last-response")
    if answer is not None:
        if answer["decision"] == "EXECUTED":
            st.success("CC-07 подтвердил исполнение. Обновите показания робота и FINAM.")
        elif answer["decision"] == "ALREADY_HALTED":
            st.info("Робот уже на PAUSE; состояние не изменялось.")
        elif answer["decision"] == "FAILED_UNKNOWN":
            st.error("Результат не подтверждён. Проверьте Task/FINAM и журнал CC-07 вручную. НЕ повторяйте команду автоматически.")
        else:
            st.error("Команда отклонена: " + answer["decision"])
    st.caption("Локальная административная панель 127.0.0.1:8502. На каждое нажатие — отдельный запрос с подтверждением, штатной проверкой CC-07 и журналом. Без фонового исполнения.")

def main():
    now = datetime.now(timezone.utc)
    if refresh:
        # Single explicit user refresh; no background gateway polling.
        st.session_state["cc07-admin-ready"] = admin_ready()
        try:
            with export_gate() as acquired:
                if acquired:
                    st.session_state["v20-source-refresh"] = refresh_once()
                    primary = acquire(datetime.now(timezone.utc))
                    if any(primary[robot]["status"] == "NOT_CONNECTED" for robot in ROBOTS):
                        staging = acquire_staging(datetime.now(timezone.utc))
                        st.session_state["v20-snapshots"] = {
                            robot: primary[robot] if primary[robot]["status"] != "NOT_CONNECTED"
                            else staging[robot] for robot in ROBOTS}
                    else:
                        st.session_state["v20-snapshots"] = primary
                else:
                    st.session_state["v20-snapshots"] = {
                        robot: unconnected(robot, "MANUAL_REFRESH_BUSY") for robot in ROBOTS}
        except Exception:
            st.session_state["v20-snapshots"] = {
                robot: unconnected(robot, "READONLY_UNAVAILABLE") for robot in ROBOTS}
        # Time of a completed manual attempt; a failed source remains NOT_CONNECTED.
        st.session_state["v20-last-checked-at"] = datetime.now(timezone.utc)
    # Always age against a clock taken AFTER manual acquisition, not before.
    now = datetime.now(timezone.utc)
    checked = st.session_state.get("v20-last-checked-at")
    last_check_view.caption("Последняя проверка: " + show_time(checked))
    if checked is not None and st.session_state.get("v20-source-refresh") not in (
        None, "READONLY_EXPORT_PASS", "PUBLISHER_UNAVAILABLE"):
        st.caption("Публикация источника: " + st.session_state["v20-source-refresh"])
    previous = st.session_state.get("v20-snapshots")
    snapshots = {}
    for robot in ROBOTS:
        report = previous[robot] if previous is not None and robot in previous else unconnected(robot)
        snapshots[robot] = age(report, now)
    if previous is not None:
        st.session_state["v20-snapshots"] = snapshots
    with tabs[0]:
        overview(snapshots, now)
    with tabs[1]:
        journal(snapshots)
    with tabs[2]:
        controls()


main()
