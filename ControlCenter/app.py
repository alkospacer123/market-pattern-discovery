"""Run from this directory: python -m streamlit run app.py."""
import streamlit as st
from cc.models import RobotId
from cc.freshness import utc_now
from cc.providers.synthetic import SCENARIOS, SyntheticProvider, read_safely
from cc.providers.h1_readonly import H1ReadonlyProvider
from cc.providers.h1_export import unchecked_export_snapshot, manual_export_refresh, age_export_snapshot
from cc.providers.h1_windows_os import manual_os_refresh
from cc.providers.h1_broker_snapshot import manual_broker_refresh, age as age_broker
from cc.ui import CSS, PAGES, render
from cc.providers.h1_operator_report import manual_published_report, age_operator_report

st.set_page_config(page_title="TradingSystemLab · Control Center", page_icon="◈", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)  # fixed local CSS only
st.caption("TRADINGSYSTEMLAB / CONTROL CENTER     ·     CC-03     ·     READ ONLY")
st.title("Центр наблюдения")
st.warning("DEMO / OFFLINE_FIXTURE — тестовые данные. WINDOWS_OS_ONLY — реальные Task/process-факты и локальный H1 CHECK при опубликованном CURRENT-отчёте. FINAM — отдельный READONLY-снимок. Управление торговлей отключено.")
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
    if h1_source == "WINDOWS_OS_ONLY":
        st.caption("H1 CHECK: оператор публикует один READONLY-отчёт в собственный каталог Control Center. Кнопка «Обновить данные» читает готовый отчёт без доступа к файлам H1.")
    st.caption("UTC / MSK (UTC+3) · локальный доступ")


def h1_operator_view(report, now):
    st.subheader("H1 · реальная локальная операторская проверка")
    if not report:
        st.info("H1 CHECK ещё не опубликован. Оператор выполняет отдельную CC-only команду публикации, затем нажимает «Обновить данные». Панель сама H1 не читает.")
        return
    report = age_operator_report(report, now)
    if report["status"] == "STALE":
        st.warning("STALE · локальный операторский отчёт устарел. Показана история, а не текущее здоровье H1.")
    else:
        st.success("LOCAL CHECK PASS · наблюдение H1. Независимая сверка позиций/стопов с FINAM этим отчётом не доказана.")
    st.caption("Heartbeat UTC: " + report["observed_at"].isoformat() + " · FINAM contact (по H1): " + report["contact_at"].isoformat())
    cols = st.columns(4)
    cols[0].metric("Цикл H1", str(report["cycle_count"]))
    cols[1].metric("Локальных позиций", str(report["positions"]))
    cols[2].metric("Локальных стопов", str(report["stops"]))
    cols[3].metric("Unresolved", str(report["unresolved"]))
    st.caption("Task: " + report["task"] + " · Kill switch: " + report["kill_switch"] + " · generation: " + report["generation"] +
               " · Health (reported): " + report["health"] + " · Reconciliation (reported): " + report["reconciliation"])
    st.subheader("Последние 10 попыток циклов H1 · PASS / FAULT")
    st.dataframe(report["cycles"], width="stretch", hide_index=True)
    st.caption("Источник: операторский локальный CHECK, не независимый брокер. Отсутствие ошибок/позиций в отчёте не доказывает брокерский FLAT, FILL или SLTP 100%. Сигналы и причины SKIP этим скриптом не публикуются.")


def live_view():
    now = utc_now()
    provider = SyntheticProvider()
    snapshots = {robot: read_safely(provider, robot, scenarios[robot], now) for robot in RobotId}
    if st.session_state.get("cc03-last-source") != h1_source:
        # Switching source clears cached positives, without invoking either source.
        st.session_state.pop("cc03-last-export", None)
        st.session_state.pop("cc03-last-broker", None)
        st.session_state.pop("cc03-local-check", None)
        st.session_state.pop("cc03-local-check-error", None)
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
            if h1_source == "WINDOWS_OS_ONLY":
                st.session_state["cc03-last-broker"] = manual_broker_refresh(utc_now())
                try:
                    st.session_state["cc03-local-check"] = manual_published_report(utc_now())
                    st.session_state.pop("cc03-local-check-error", None)
                except (ValueError, OSError):
                    st.session_state.pop("cc03-local-check", None)
                    st.session_state["cc03-local-check-error"] = True
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
    broker = age_broker(st.session_state.get('cc03-last-broker'), now) if h1_source == 'WINDOWS_OS_ONLY' else None
    if h1_source == 'WINDOWS_OS_ONLY' and 'cc03-last-broker' in st.session_state:
        st.session_state['cc03-last-broker'] = broker
    local_report = None
    if h1_source == "WINDOWS_OS_ONLY" and "cc03-local-check" in st.session_state:
        local_report = age_operator_report(st.session_state["cc03-local-check"], now)
        st.session_state["cc03-local-check"] = local_report
    render(page, snapshots, now, broker=broker, local_report=local_report)
    if h1_source == "WINDOWS_OS_ONLY" and page in (PAGES[0], PAGES[1]):
        if st.session_state.get("cc03-local-check-error"):
            st.warning("H1 CHECK: отчёт неполный, устарел по структуре или содержит FAIL. Ничего не принято.")
        h1_operator_view(local_report, now)


live_view()
