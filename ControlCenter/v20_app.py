"""V20 operator-only Streamlit entrypoint. The legacy Intel app.py is unchanged."""
from datetime import datetime, timedelta, timezone
import streamlit as st
from cc.manual_gate import export_gate
from cc.v20_contract import ROBOTS, LABELS, unconnected, age
from cc.v20_receiver import acquire

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
tabs = st.tabs(PAGES)


def show_time(at):
    return at.astimezone(MSK).strftime("%d.%m.%Y %H:%M:%S МСК") if at else "—"


def healthy_label(report):
    status = report["status"]
    return {"HEALTHY": "HEALTHY", "HALTED": "HALTED", "FAULT": "FAULT",
            "UNKNOWN": "UNKNOWN", "STALE": "STALE",
            "NOT_CONNECTED": "НЕ ПОДКЛЮЧЁН"}.get(status, "UNKNOWN")


def overview(snapshots):
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
                if current:
                    st.markdown("**Windows Task:** " + report["task_state"] +
                                " · **Kill switch:** " + report["kill_switch"])
                    error_code = report["last_error_code"]
                    st.caption("Heartbeat: " + show_time(report["heartbeat_at"]) +
                               " · Последняя ошибка: " +
                               ("нет" if error_code == "NONE" else error_code))
                elif status == "STALE":
                    st.caption("Heartbeat: " + show_time(report["heartbeat_at"]) +
                               " (устарел) · текущее состояние Task/защиты не подтверждено")
                else:
                    st.caption("Нет подтверждённых данных о задаче, heartbeat и ошибках")
    with st.expander("Об источниках", expanded=False):
        st.caption("Состояния приходят только из отдельных READONLY-отчётов V20. Пока источники не подключены, работоспособность неизвестна.")
        st.caption("HEALTHY означает состояние по локальному отчёту; не подтверждает сделки, брокерские позиции и SLTP FINAM.")
        st.caption("Обновление только вручную; панель не получает торговые токены и не исполняет команды.")


def journal(snapshots):
    st.subheader("Последние циклы")
    for robot in ROBOTS:
        report = snapshots[robot]
        with st.expander(LABELS[robot] + " · " + healthy_label(report), expanded=False):
            if report["events"]:
                st.dataframe([{"Время": show_time(event["at"]),
                               "Цикл": event["cycle"], "Результат": event["result"],
                               "Причина": event["code"]} for event in report["events"]],
                             hide_index=True, width="stretch")
            else:
                st.caption("Подтверждённых событий пока нет")
            if report["status"] == "STALE":
                st.caption("Исторические события · снимок STALE")


def controls():
    st.subheader("Управление")
    st.info("Отключено. Команды START / PAUSE / STOP / RESTART появятся только после отдельной приёмки контроллера для трёх V20-роботов.")
    st.caption("Нет торговых полномочий, обработчиков команд и доступа к Windows Task.")


def main():
    now = datetime.now(timezone.utc)
    if refresh:
        try:
            with export_gate() as acquired:
                if acquired:
                    st.session_state["v20-snapshots"] = acquire(datetime.now(timezone.utc))
                else:
                    st.session_state["v20-snapshots"] = {
                        robot: unconnected(robot, "MANUAL_REFRESH_BUSY") for robot in ROBOTS}
        except Exception:
            st.session_state["v20-snapshots"] = {
                robot: unconnected(robot, "READONLY_UNAVAILABLE") for robot in ROBOTS}
    # Always age against a clock taken AFTER manual acquisition, not before.
    now = datetime.now(timezone.utc)
    previous = st.session_state.get("v20-snapshots")
    snapshots = {}
    for robot in ROBOTS:
        report = previous[robot] if previous is not None and robot in previous else unconnected(robot)
        snapshots[robot] = age(report, now)
    if previous is not None:
        st.session_state["v20-snapshots"] = snapshots
    with tabs[0]:
        overview(snapshots)
    with tabs[1]:
        journal(snapshots)
    with tabs[2]:
        controls()


main()
