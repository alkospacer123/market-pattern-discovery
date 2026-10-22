"""Selection authority: IntradayLab/SELECTED_T3_M15_SESSION_T1_R15.md.

These are frozen selection constants, not H1 TradingSystemLab production identity.
Never silently substitute A6+S1, SIGNAL_CLOSE, or R20.
"""
from decimal import Decimal

ROBOT_ID = "T3_M15_T1_TRAIL35_N4_R15"
RESEARCH_BUILD_ID = "T1_NEXT_OPEN_TRAIL_3p5"
INSTRUMENTS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
ENTRY_MODEL = "NEXT_OPEN"
TIMEFRAME_MINUTES = 15
SIGNAL_START_MSK_MINUTE = 10 * 60
SIGNAL_END_MSK_MINUTE = 18 * 60  # exclusive
INITIAL_STOP_ATR = Decimal("2")
TRAILING_STOP_ATR = Decimal("3.5")
RISK_FRACTION = Decimal("0.015")
MAX_NOMINAL_INITIAL_RISK = Decimal("0.06")
MAX_OPEN_INSTRUMENTS = 4
EXECUTION_STATUS = "NOT_LIVE_AUTHORIZED"
