"""Run from this directory: python -m streamlit run app.py."""
import streamlit as st
from cc.models import RobotId
from cc.freshness import utc_now
from cc.providers.synthetic import SCENARIOS, SyntheticProvider, read_safely
from cc.providers.h1_readonly import H1ReadonlyProvider
from cc.providers.h1_export import unchecked_export_snapshot, manual_export_refresh, age_export_snapshot
from cc.providers.h1_windows_os import manual_os_refresh
from cc.ui import CSS, PAGES, render

st.set_page_config(page_title="TradingSystemLab · Control Center DEMO", page_icon="◈", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)  # fixed local CSS only
st.caption("TRADINGSYSTEMLAB / CONTROL CENTER     ·     CC-03     ·     READ ONLY")
st.title("Центр наблюдения")
st.warning("SYNTHETIC / DEMO и OFFLINE_FIXTURE — тестовые данные. WINDOWS_OS_ONLY — ручные Task/process-факты с отдельной policy. Состояние робота и broker authority UNKNOWN. Торговля запрещена.")
with st.sidebar:
    st.title("◈ Control Center")
    st.caption("Два робота. Независимые контуры.")
    page = st.radio("Раздел", PAGES)
    st.divider()
    h1_source = st.selectbox("Источник H1", ("SYNTHETIC / DEMO", "OFFLINE_FIXTURE", "READONLY_EXPORT", "WINDOWS_OS_ONLY"), key="h1-source")
    st.caption("WINDOWS_OS_ONLY: одна ручная диагностика Windows Task/process. Без отдельной утверждённой policy C — UNKNOWN. READONLY_EXPORT: отдельный очищенный снимок.")
    st.subheader("Локальные сценарии DEMO")
    scenarios = {robot: st.selectbox(f"Сценарий {robot}", list(SCENARIOS), format_func=SCENARIOS.get,
                                    key=f"scenario-{robot}") for robot in RobotId}
    manual_refresh = st.button("Обновить данные", key="cc03-manual-refresh",
                               disabled=h1_source not in ("READONLY_EXPORT", "WINDOWS_OS_ONLY"))
    st.caption("Только по кнопке; без таймеров и повторов. WINDOWS_OS_ONLY не читает heartbeat/файлы H1. FINAM не вызывается. Снимок истекает по TTL при следующем отображении.")
    st.caption("DEMO и OFFLINE_FIXTURE — тестовые локальные данные. M15 остаётся NOT_DEPLOYED.")
    st.caption("UTC / MSK (UTC+3) · локальный доступ")


def live_view():
    now = utc_now()
    provider = SyntheticProvider()
    snapshots = {robot: read_safely(provider, robot, scenarios[robot], now) for robot in RobotId}
    if st.session_state.get("cc03-last-source") != h1_source:
        # Switching source clears cached positives, without invoking either source.
        st.session_state.pop("cc03-last-export", None)
        st.session_state["cc03-last-source"] = h1_source
    if h1_source == "OFFLINE_FIXTURE":
        snapshots[RobotId.H1] = H1ReadonlyProvider().snapshot(RobotId.H1, "OFFLINE_FIXTURE", now)
    elif h1_source in ("READONLY_EXPORT", "WINDOWS_OS_ONLY"):
        # Zero source I/O on startup, navigation or reruns. Both modes share the
        # nonblocking per-SID cross-process/session gate BEFORE policy/identity I/O.
        if manual_refresh:
            refresh = manual_os_refresh if h1_source == "WINDOWS_OS_ONLY" else manual_export_refresh
            snapshot, accepted = refresh(now)
            st.session_state["cc03-last-export"] = snapshot
            if not accepted:
                st.warning("BLOCKED / UNKNOWN · " + snapshot.events[0].message +
                           ": источник недоступен, policy не принята или другая ручная проверка выполняется. Автоматического повтора нет.")
        now = utc_now()
        snapshots[RobotId.H1] = age_export_snapshot(
            st.session_state.get("cc03-last-export") or unchecked_export_snapshot(
                now, windows_os=h1_source == "WINDOWS_OS_ONLY"), now)
        if "cc03-last-export" in st.session_state:
            # Expiry/clock failure permanently clears cached positives until a
            # new explicit click. A later clock rewind must not revive them.
            st.session_state["cc03-last-export"] = snapshots[RobotId.H1]
        if "cc03-last-export" not in st.session_state:
            st.info("Проверка H1 не запускалась. Нажмите «Обновить данные»; без утверждённого источника результат останется UNKNOWN.")
    render(page, snapshots, now)


live_view()
