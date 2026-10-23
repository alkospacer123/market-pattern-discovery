"""V20 operator-only Streamlit entrypoint. The legacy Intel app.py is unchanged."""
from datetime import datetime, timedelta, timezone
import streamlit as st
from cc.manual_gate import export_gate
from cc.v20_contract import ROBOTS, LABELS, unconnected, age
from cc.v20_receiver import acquire

MSK = timezone(timedelta(hours=3))
PAGES = ("Главная", "Журнал", "Управление")

st.set_page_config(page_title="V20 · Control Center", page_icon="◈", layout="wide")
st.title("V20 · Control Center")
st.caption("Shallow · OBV · Inside | один проект, три независимых робота")
with st.sidebar:
    page = st.radio("Раздел", PAGES, label_visibility="collapsed")
    refresh = st.button("Обновить данные", key="v20-manual-refresh",
                        use_container_width=True)
    st.caption("READONLY · только вручную")


def show_time(at):
    return at.astimezone(MSK).strftime("%d.%m.%Y %H:%M:%S МСК") if at else "—"


def healthy_label(report):
    status = report["status"]
    return {"HEALTHY": "HEALTHY", "HALTED": "HALTED", "FAULT": "FAULT",
            "UNKNOWN": "UNKNOWN", "STALE": "STALE",
            "NOT_CONNECTED": "НЕ ПОДКЛЮЧЁН"}.get(status, "UNKNOWN")


def overview(snapshots):
    for robot in ROBOTS:
        report = snapshots[robot]
        with st.container(border=True):
            left, right = st.columns([2, 3])
            with left:
                st.subheader(LABELS[robot])
                if report["status"] == "HEALTHY":
                    st.success(healthy_label(report))
                elif report["status"] in ("STALE", "FAULT"):
                    st.warning(healthy_label(report))
                else:
                    st.info(healthy_label(report))
                st.caption("Heartbeat: " + show_time(report["heartbeat_at"]))
            with right:
                a, b, c = st.columns(3)
                a.metric("Цикл", str(report["cycle"]) if report["status"] not in ("STALE", "NOT_CONNECTED", "UNKNOWN") and report["cycle"] is not None else "—")
                b.metric("Позиции · локально", str(report["positions_local"]) if report["status"] not in ("STALE", "NOT_CONNECTED", "UNKNOWN") and report["positions_local"] is not None else "—")
                c.metric("Стопы · локально", str(report["stops_local"]) if report["status"] not in ("STALE", "NOT_CONNECTED", "UNKNOWN") and report["stops_local"] is not None else "—")
                st.caption("Task: " + report["task_state"] + " · Ошибка: " +
                           report["last_error_code"] + " · Снимок: " +
                           show_time(report["observed_at"]))
    with st.expander("Источники и ограничения", expanded=False):
        st.caption("Состояние каждого робота приходит только из собственного CC READONLY-снимка. На этапе V20-04 реальные источники ещё не подключены.")
        st.caption("Локальные позиции/стопы не являются независимой брокерской сверкой FINAM. Нет подтверждения исполнения, SLTP и торговой авторизации.")
        st.caption("Панель не получает торговые токены и не отправляет заявки. Никаких автоматических запросов или фонового обновления.")


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
    previous = st.session_state.get("v20-snapshots")
    snapshots = {}
    for robot in ROBOTS:
        report = previous[robot] if previous is not None and robot in previous else unconnected(robot)
        snapshots[robot] = age(report, now)
    if previous is not None:
        st.session_state["v20-snapshots"] = snapshots
    if page == PAGES[0]:
        overview(snapshots)
    elif page == PAGES[1]:
        journal(snapshots)
    else:
        controls()


main()
