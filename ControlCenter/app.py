"""Run from this directory: python -m streamlit run app.py."""
from datetime import datetime, timezone
import streamlit as st
from cc.models import RobotId
from cc.providers.synthetic import SCENARIOS, SyntheticProvider, read_safely
from cc.ui import CSS, PAGES, render

st.set_page_config(page_title="TradingSystemLab · Control Center DEMO", page_icon="◈", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)  # fixed local CSS only
st.caption("TRADINGSYSTEMLAB / CONTROL CENTER     ·     CC-00 + CC-01     ·     READ ONLY")
st.title("Центр наблюдения")
st.warning("SYNTHETIC / DEMO — все цены, сигналы, сделки и капиталы искусственные. Торговые системы не подключены. Торговля запрещена.")
with st.sidebar:
    st.title("◈ Control Center")
    st.caption("Два робота. Независимые контуры.")
    page = st.radio("Раздел", PAGES)
    st.divider()
    st.subheader("Локальные сценарии DEMO")
    scenarios = {robot: st.selectbox(f"Сценарий {robot}", list(SCENARIOS), format_func=SCENARIOS.get,
                                    key=f"scenario-{robot}") for robot in RobotId}
    automatic = st.checkbox("Автообновление каждые 2 секунды", value=True)
    st.caption("Обновляются только синтетические снимки в памяти. M15 всегда NOT_DEPLOYED; его production-параметры UNKNOWN.")
    st.caption("UTC / MSK (UTC+3) · локальный доступ")


@st.fragment(run_every=2 if automatic else None)
def live_view():
    now = datetime.now(timezone.utc)
    provider = SyntheticProvider()
    snapshots = {robot: read_safely(provider, robot, scenarios[robot], now) for robot in RobotId}
    render(page, snapshots, now)


live_view()
