"""Run from this directory: python -m streamlit run app.py."""
from datetime import datetime, timezone
import streamlit as st
from cc.models import RobotId
from cc.providers.synthetic import SCENARIOS, SyntheticProvider, read_safely
from cc.providers.h1_readonly import H1ReadonlyProvider
from cc.ui import CSS, PAGES, render

st.set_page_config(page_title="TradingSystemLab · Control Center DEMO", page_icon="◈", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)  # fixed local CSS only
st.caption("TRADINGSYSTEMLAB / CONTROL CENTER     ·     CC-02     ·     READ ONLY")
st.title("Центр наблюдения")
st.warning("SYNTHETIC / DEMO и OFFLINE_FIXTURE — тестовые данные. Торговые системы не подключены. Торговля запрещена.")
with st.sidebar:
    st.title("◈ Control Center")
    st.caption("Два робота. Независимые контуры.")
    page = st.radio("Раздел", PAGES)
    st.divider()
    h1_source = st.selectbox("Источник H1", ("SYNTHETIC / DEMO", "OFFLINE_FIXTURE"), key="h1-source")
    st.caption("OFFLINE_FIXTURE читает только поставляемый тестовый JSON. LIVE-источник недоступен в CC-02.")
    st.subheader("Локальные сценарии DEMO")
    scenarios = {robot: st.selectbox(f"Сценарий {robot}", list(SCENARIOS), format_func=SCENARIOS.get,
                                    key=f"scenario-{robot}") for robot in RobotId}
    automatic = st.checkbox("Автообновление каждые 2 секунды", value=True)
    st.caption("Обновляются DEMO или фиксированный локальный H1 fixture; время файла не освежается. M15 всегда NOT_DEPLOYED; его production-параметры UNKNOWN.")
    st.caption("UTC / MSK (UTC+3) · локальный доступ")


@st.fragment(run_every=2 if automatic else None)
def live_view():
    now = datetime.now(timezone.utc)
    provider = SyntheticProvider()
    snapshots = {robot: read_safely(provider, robot, scenarios[robot], now) for robot in RobotId}
    if h1_source == "OFFLINE_FIXTURE":
        snapshots[RobotId.H1] = H1ReadonlyProvider().snapshot(RobotId.H1, "OFFLINE_FIXTURE", now)
    render(page, snapshots, now)


live_view()
