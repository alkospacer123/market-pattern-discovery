"""PR #493 task 1.2. All FINAM responses and order ACKs are synthetic.

No credentials, network calls, LIVE Task, local production SQLite or real
order endpoints. The write gate is a test callback, NEVER operator approval.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256

import pytest

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.diagnostics.stage8_493_operator_harness import (
    Hold, Journal, OperatorHarness, Plan,
)
from TradingSystemLab.stage8_robot.diagnostics.stage8_493_finam_operator_port import (
    FinamOperatorPort,
)

ACCOUNT = "synthetic-operator-account"
SYMBOL = "CNYRUBF@RTSX"


def plan():
    return Plan(sha256(ACCOUNT.encode()).hexdigest(), "CNYRUBF", SYMBOL, "LONG",
                "acceptance:entry:1", "acceptance:stop:1", "12.740")


class FakeFINAM:
    def __init__(self, *, readonly=False):
        self.readonly = readonly
        self.account_id = ACCOUNT
        self.position = 0
        self.entry_submissions = []
        self.stop_submissions = []
        self.cancel_submissions = []
        self.entry_status = "ORDER_STATUS_PARTIAL_FILL"
        self.entry_remaining = 1
        self.stop_status = "ORDER_STATUS_NEW"
        self.fill_qty = 1
        self.created_session = False
        self.fill_time = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        self.history_queries = []

    def create_session(self):
        self.created_session = True
        return {}

    def session_details(self):
        assert self.created_session
        return {"readonly": self.readonly, "account_ids": [self.account_id]}

    def account(self, account_id):
        assert account_id == self.account_id
        return {"account_id": account_id, "status": "ACCOUNT_ACTIVE",
                "positions": [{"symbol": SYMBOL, "quantity": {"value": str(self.position)}}]}

    def orders(self, account_id):
        assert account_id == self.account_id
        rows = []
        if self.entry_submissions:
            rows.append({"order_id": "finam-entry-1", "status": self.entry_status,
                         "order": self.entry_submissions[0],
                         "remaining_quantity": {"value": str(self.entry_remaining)}})
        if self.stop_submissions:
            rows.append({"order_id": "finam-stop-1", "status": self.stop_status,
                         "sltp_order": self.stop_submissions[0]})
        return {"orders": rows}

    def trades(self, account_id, *, start, end, limit):
        assert account_id == self.account_id
        self.history_queries.append((start, end, limit))
        rows = []
        for i in range(self.fill_qty):
            rows.append({"order_id": "finam-entry-1", "account_id": ACCOUNT,
                         "symbol": SYMBOL, "side": "SIDE_BUY", "trade_id": "fill-"+str(i),
                         "size": {"value": "1"}, "price": {"value": "12.750"},
                         "timestamp": self.fill_time, "currency": "XXX"})
        return {"trades": rows}

    def place_order(self, account_id, payload):
        assert account_id == ACCOUNT
        self.entry_submissions.append(payload)
        if payload["side"] == "SIDE_BUY":
            self.position = 1
            return {"order_id": "finam-entry-1"}
        self.position = 0
        return {"order_id": "finam-exit-1"}

    def place_sltp_order(self, account_id, payload):
        assert account_id == ACCOUNT
        self.stop_submissions.append(payload)
        return {"order_id": "finam-stop-1"}

    def cancel_order(self, account_id, order_id):
        self.cancel_submissions.append((account_id, order_id))
        return {"order_id": order_id}


def port(api=None, gate=None):
    api = api or FakeFINAM()
    history_start = (datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat()
    instance = FinamOperatorPort(api=api, account_id=ACCOUNT, plan=plan(),
                                 history_start=history_start, operator_write_gate=gate)
    instance.connect()
    return instance, api


def permit(action, bound_plan):
    assert action in {"ENTRY", "SLTP", "CANCEL", "EXIT"}
    assert bound_plan == plan()


def test_default_readonly_observation_and_write_denial():
    bridge, api = port()
    obs = bridge.observe()
    assert obs["position"] == 0 and obs["orders"] == []
    with pytest.raises(Hold, match="REAL_ORDER_GATE_NOT_AUTHORIZED"):
        bridge.entry(key=plan().entry_key, symbol=SYMBOL, side="SIDE_BUY", quantity=2)
    assert api.entry_submissions == [] and api.stop_submissions == []


def test_readonly_trading_token_blocks_write_even_with_synthetic_callback():
    bridge, api = port(FakeFINAM(readonly=True), permit)
    with pytest.raises(Hold, match="REAL_ORDER_GATE_NOT_AUTHORIZED"):
        bridge.entry(key=plan().entry_key, symbol=SYMBOL, side="SIDE_BUY", quantity=2)
    assert api.entry_submissions == []


def test_account_binding_mismatch_fails_before_endpoint():
    api = FakeFINAM()
    api.account_id = "wrong-account"
    with pytest.raises(Hold, match="FINAM_OPERATOR_SESSION_NOT_ACCOUNT_BOUND"):
        port(api, permit)
    assert api.entry_submissions == []


def test_operator_harness_with_finam_adapter_is_sticky_inconclusive(tmp_path):
    bridge, api = port(FakeFINAM(), permit)
    audit = Journal(tmp_path / "audit", fresh=True)
    op = OperatorHarness(plan(), bridge, audit)
    assert op.entry_and_growth() == "STOP_AT_ONE_OBSERVED_GROWTH_PENDING"
    assert len(api.entry_submissions) == 1 and len(api.stop_submissions) == 1
    assert api.entry_submissions[0]["type"] == "ORDER_TYPE_MARKET"
    assert api.entry_submissions[0]["quantity"] == {"value": "2"}
    stop = api.stop_submissions[0]
    assert stop["sl_qty_measure"] == "SLTP_QTY_MEASURE_PERCENT"
    assert stop["quantity_sl"] == {"value": "100"}
    assert stop["comment"] == plan().stop_key
    assert stop["client_order_id"] == compact_client_order_id(plan().stop_key)
    assert api.history_queries and api.history_queries[-1][2] == 1000

    api.position = 2
    api.entry_remaining = 0
    api.entry_status = "ORDER_STATUS_FILLED"
    api.fill_qty = 2
    assert op.observe_growth() == "INCONCLUSIVE_REAL_STOP_TRIGGER_NOT_PROVEN"
    assert audit.count("growth_observed") == 1

    restarted = OperatorHarness(plan(), bridge, Journal(audit.root, fresh=False))
    with pytest.raises(Hold, match="JOURNAL_ALREADY_USED_NO_REPLAY"):
        restarted.entry_and_growth()
    assert len(api.entry_submissions) == 1


def test_no_retry_when_ack_unknown_and_harness_journal_sticky(tmp_path):
    api = FakeFINAM()
    def uncertain(account_id, payload):
        api.entry_submissions.append(payload)
        raise TimeoutError("synthetic-ack-unknown")
    api.place_order = uncertain
    bridge, api = port(api, permit)
    audit = Journal(tmp_path / "audit", fresh=True)
    op = OperatorHarness(plan(), bridge, audit)
    with pytest.raises(Hold, match="ENTRY_ACK_OR_TRANSPORT_UNKNOWN"):
        op.entry_and_growth()
    with pytest.raises(Hold, match="JOURNAL_ALREADY_USED_NO_REPLAY"):
        op.entry_and_growth()
    assert len(api.entry_submissions) == 1
    with pytest.raises(Hold):
        bridge.entry(key=plan().entry_key, symbol=SYMBOL, side="SIDE_BUY", quantity=2)
    assert len(api.entry_submissions) == 1


def test_fill_contract_missing_refuses_protection(tmp_path):
    bridge, api = port(FakeFINAM(), permit)
    api.fill_qty = 0
    op = OperatorHarness(plan(), bridge, Journal(tmp_path / "audit", fresh=True))
    with pytest.raises(Hold, match="FILL_HISTORY_MISSING"):
        op.entry_and_growth()
    assert len(api.entry_submissions) == 1 and len(api.stop_submissions) == 0


def test_stop_cancel_requires_flat_and_exact_broker_order():
    bridge, api = port(FakeFINAM(), permit)
    bridge.entry(key=plan().entry_key, symbol=SYMBOL, side="SIDE_BUY", quantity=2)
    bridge.install_stop(key=plan().stop_key, symbol=SYMBOL,
                        side="SIDE_SELL", price=plan().stop_price, percent=100)
    with pytest.raises(Hold, match="OPERATOR_CANCEL_NOT_SAFE"):
        bridge.cancel("finam-stop-1")
    assert api.cancel_submissions == []
    api.position = 0
    # Flatness alone is insufficient: entry remainder can still fill.
    with pytest.raises(Hold, match="OPERATOR_CANCEL_NOT_SAFE"):
        bridge.cancel("finam-stop-1")
    api.entry_status = "ORDER_STATUS_CANCELLED"
    api.entry_remaining = 0
    assert bridge.cancel("finam-stop-1") == "CANCEL_ACK_NOT_TERMINAL_PROOF"
    assert api.cancel_submissions == [(ACCOUNT, "finam-stop-1")]


def test_exit_never_races_live_sltp():
    bridge, api = port(FakeFINAM(), permit)
    bridge.entry(key=plan().entry_key, symbol=SYMBOL, side="SIDE_BUY", quantity=2)
    bridge.install_stop(key=plan().stop_key, symbol=SYMBOL,
                        side="SIDE_SELL", price=plan().stop_price, percent=100)
    with pytest.raises(Hold, match="OPERATOR_EXIT_REQUIRES_TERMINAL_ORDER_PROOF"):
        bridge.exit(key="manual-exit", symbol=SYMBOL, side="SIDE_SELL", quantity=1)
    assert len(api.entry_submissions) == 1


def test_wrong_stop_side_quantity_and_unknown_cancel_never_post():
    bridge, api = port(FakeFINAM(), permit)
    with pytest.raises(Hold):
        bridge.entry(key=plan().entry_key, symbol=SYMBOL, side="SIDE_SELL", quantity=2)
    with pytest.raises(Hold):
        bridge.entry(key=plan().entry_key, symbol=SYMBOL, side="SIDE_BUY", quantity=3)
    with pytest.raises(Hold):
        bridge.cancel("unknown-order-id")
    assert api.entry_submissions == [] and api.cancel_submissions == []


def test_operator_recovery_exit_after_order_reconciliation_and_final_double_flat(tmp_path):
    """OFFLINE fake: an exit must never race the active protective stop.

    Broker-terminal reconciliation precedes the permitted synthetic exit;
    the final two reads must establish terminal entry AND stop orders.
    This is NOT evidence that FINAM can physically execute this procedure.
    """
    bridge, api = port(FakeFINAM(), permit)
    audit = Journal(tmp_path / "audited-operator-recovery", fresh=True)
    operator = OperatorHarness(plan(), bridge, audit)
    assert operator.entry_and_growth() == "STOP_AT_ONE_OBSERVED_GROWTH_PENDING"
    assert len(api.entry_submissions) == 1 and len(api.stop_submissions) == 1
    # While the stop is active the program must not race a market exit.
    with pytest.raises(Hold, match="OPERATOR_EXIT_REQUIRES_TERMINAL_ORDER_PROOF"):
        bridge.exit(key="recovery:flatten:1", symbol=SYMBOL,
                    side="SIDE_SELL", quantity=1)
    assert len(api.entry_submissions) == 1
    # Synthetic externally reconciled broker-terminal statuses.
    api.entry_status = "ORDER_STATUS_CANCELLED"
    api.entry_remaining = 0
    api.stop_status = "ORDER_STATUS_CANCELLED"
    # Synthetic exit only after both entry remainder and stop are inactive.
    assert bridge.exit(key="recovery:flatten:1", symbol=SYMBOL,
                       side="SIDE_SELL", quantity=1) == "finam-exit-1"
    assert api.position == 0
    assert len(api.entry_submissions) == 2
    with pytest.raises(Hold, match="OPERATOR_EXIT_REQUIRES_TERMINAL_ORDER_PROOF"):
        bridge.exit(key="recovery:flatten:1", symbol=SYMBOL,
                    side="SIDE_SELL", quantity=1)
    assert len(api.entry_submissions) == 2
    assert operator.final_flat() == "FLAT_AFTER_MANUAL_RECOVERY_NOT_PHYSICAL_SLTP_ACCEPTANCE"
    assert audit.count("double_flat") == 1
    assert len(api.cancel_submissions) == 0


def test_operator_unknown_exit_ack_stays_sticky_no_second_market_post():
    bridge, api = port(FakeFINAM(), permit)
    bridge.entry(key=plan().entry_key, symbol=SYMBOL, side="SIDE_BUY", quantity=2)
    api.entry_status = "ORDER_STATUS_CANCELLED"
    api.entry_remaining = 0
    def uncertain(account_id, payload):
        api.entry_submissions.append(payload)
        raise TimeoutError("synthetic-flatten-ack-uncertain")
    api.place_order = uncertain
    with pytest.raises(TimeoutError, match="synthetic-flatten-ack-uncertain"):
        bridge.exit(key="recovery:exit:uncertain", symbol=SYMBOL,
                    side="SIDE_SELL", quantity=1)
    count=len(api.entry_submissions)
    with pytest.raises(Hold, match="REAL_ORDER_OPERATION_OR_KEY_INVALID"):
        bridge.exit(key="recovery:exit:uncertain", symbol=SYMBOL,
                    side="SIDE_SELL", quantity=1)
    assert len(api.entry_submissions) == count
