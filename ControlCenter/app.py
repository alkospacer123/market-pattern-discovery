"""Run from this directory: python -m streamlit run app.py."""
from datetime import datetime, timezone
import streamlit as st
from cc.models import RobotId
from cc.providers.synthetic import SCENARIOS, SyntheticProvider, read_safely
from cc.providers.h1_readonly import H1ReadonlyProvider
from cc.providers.h1_export import unchecked_export_snapshot, manual_export_refresh
from cc.ui import CSS, PAGES, render

st.set_page_config(page_title="TradingSystemLab · Control Center DEMO", page_icon="◈", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)  # fixed local CSS only
st.caption("TRADINGSYSTEMLAB / CONTROL CENTER     ·     CC-03     ·     READ ONLY")
st.title("Центр наблюдения")
st.warning("SYNTHETIC / DEMO и OFFLINE_FIXTURE — тестовые данные. READONLY_EXPORT требует отдельно принятого источника; broker authority UNKNOWN. Торговля запрещена.")
with st.sidebar:
    st.title("◈ Control Center")
    st.caption("Два робота. Независимые контуры.")
    page = st.radio("Раздел", PAGES)
    st.divider()
    h1_source = st.selectbox("Источник H1", ("SYNTHETIC / DEMO", "OFFLINE_FIXTURE", "READONLY_EXPORT"), key="h1-source")
    st.caption("OFFLINE_FIXTURE читает только поставляемый тестовый JSON. READONLY_EXPORT читает только отдельный очищенный снимок; без утверждённой policy — UNKNOWN.")
    st.subheader("Локальные сценарии DEMO")
    scenarios = {robot: st.selectbox(f"Сценарий {robot}", list(SCENARIOS), format_func=SCENARIOS.get,
                                    key=f"scenario-{robot}") for robot in RobotId}
    manual_refresh = st.button("Обновить данные", key="cc03-manual-refresh",
                               disabled=h1_source != "READONLY_EXPORT")
    st.caption("Кнопка перечитывает только отдельный снимок Control Center. H1, FINAM и Task не вызываются. Пока нет утверждённого источника — UNKNOWN.")
    st.caption("DEMO и OFFLINE_FIXTURE — тестовые локальные данные. M15 остаётся NOT_DEPLOYED.")
    st.caption("UTC / MSK (UTC+3) · локальный доступ")


def live_view():
    now = datetime.now(timezone.utc)
    provider = SyntheticProvider()
    snapshots = {robot: read_safely(provider, robot, scenarios[robot], now) for robot in RobotId}
    if h1_source != "READONLY_EXPORT":
        # Neither page navigation nor switching back to DEMO may retain a LIVE-looking export.
        st.session_state.pop("cc03-last-export", None)
    if h1_source == "OFFLINE_FIXTURE":
        snapshots[RobotId.H1] = H1ReadonlyProvider().snapshot(RobotId.H1, "OFFLINE_FIXTURE", now)
    elif h1_source == "READONLY_EXPORT":
        # No call to the export receiver until the operator explicitly clicks once.
        # The receiver reads only Control Center's isolated export root, not H1.
        if manual_refresh:
            snapshot, accepted = manual_export_refresh(now)
            st.session_state["cc03-last-export"] = snapshot
            if not accepted:
                st.warning("BLOCKED: предыдущая ручная проверка ещё выполняется или источник недоступен. Новая проверка не запускалась.")
        snapshots[RobotId.H1] = st.session_state.get("cc03-last-export") or unchecked_export_snapshot(now)
        if "cc03-last-export" not in st.session_state:
            st.info("Проверка H1 не запускалась. Нажмите «Обновить данные»; без утверждённого источника результат останется UNKNOWN.")
    render(page, snapshots, now)


live_view()
