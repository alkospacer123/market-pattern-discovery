"""V20-08.1 broker-side adapter using existing, unchanged H1 FINAM readers.

The OFFLINE FakeBroker runner and three Disabled Windows Tasks are NOT replaced.
This module has no order/SLTP/cancel methods, credential store or authorization
writer. In particular it must never be treated as proof of executable LIVE.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import re
from typing import Any

from TradingSystemLab.stage8_robot.finam_api import FinamAPI
from TradingSystemLab.stage8_robot.margin import (
    directional_initial_margin,
    parse_rest_decimal_value_object,
    portfolio_authority,
)
from TradingSystemLab.stage8_robot.production_broker_state import (
    BrokerOrderView, order_views, position_quantities,
)
from TradingSystemLab.stage8_robot.production_runtime import _load_registry

from .account_risk import AccountAuthority
from .h1_state_journal import ROBOT_STRATEGIES
from .offline_planner import N4


ACTIVE_STATUSES = frozenset({"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"})


class V20FinamBlocked(RuntimeError):
    """No implicit cross-account, estimated or unverified FINAM authority."""


@dataclass(frozen=True)
class LiveAccountSnapshot:
    robot_id: str
    account_hash: str
    observed_at: datetime
    realized_equity: Decimal
    available_cash: Decimal
    positions: dict[str, int]
    orders: tuple[BrokerOrderView, ...]

    @property
    def clean(self) -> bool:
        return not self.positions and not any(order.active for order in self.orders)


class V20FinamReadAdapter:
    """One instance per FINAM account; all network traffic uses H1 FinamAPI.

    Its only network operations are session auth, account GET, orders GET and
    four N4 account-scoped asset-params GETs. Before actual LIVE, V20 must
    separately implement durable order intents and user-scoped authorization.
    """

    def __init__(
        self, *, api: FinamAPI, robot_id: str, account_id: str,
        expected_account_hash: str,
    ):
        if robot_id not in ROBOT_STRATEGIES:
            raise V20FinamBlocked("UNKNOWN_V20_ROBOT")
        if (not isinstance(account_id, str)
                or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account_id)
                or not re.fullmatch(r"[0-9a-f]{64}", str(expected_account_hash))
                or hashlib.sha256(account_id.encode("utf-8")).hexdigest() != expected_account_hash):
            raise V20FinamBlocked("ACCOUNT_IDENTITY_MISMATCH")
        if not isinstance(api, FinamAPI):
            raise V20FinamBlocked("H1_FINAM_API_REQUIRED")
        self.api = api
        self.robot_id = robot_id
        self.account_id = account_id
        self.account_hash = expected_account_hash
        self._bound = False

    def authenticate(self) -> None:
        self._bound = False
        self.api.create_session()
        details = self.api.session_details()
        ids = details.get("account_ids") if isinstance(details, dict) else None
        if (not isinstance(ids, list) or ids.count(self.account_id) != 1
                or details.get("readonly") is not False):
            raise V20FinamBlocked("EXACT_TRADING_TOKEN_SCOPE_REQUIRED")
        self._bound = True

    def _require_bound(self) -> None:
        if not self._bound:
            raise V20FinamBlocked("TRADING_SESSION_NOT_BOUND")

    def snapshot(self, *, now: datetime) -> LiveAccountSnapshot:
        self._require_bound()
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise V20FinamBlocked("UTC_OBSERVATION_REQUIRED")
        raw = self.api.account(self.account_id)
        if (not isinstance(raw, dict) or raw.get("account_id") != self.account_id
                or raw.get("status") not in ACTIVE_STATUSES):
            raise V20FinamBlocked("FINAM_ACCOUNT_RESPONSE_INVALID")
        positions = position_quantities(raw)
        orders = order_views(self.api.orders(self.account_id))
        known = {x["finam_symbol"] for x in _load_registry().values()}
        if any(symbol not in known for symbol in positions):
            raise V20FinamBlocked("FOREIGN_ACCOUNT_POSITION")
        if any(order.active and order.symbol not in known for order in orders):
            raise V20FinamBlocked("UNKNOWN_ACTIVE_ACCOUNT_ORDER")
        funds = portfolio_authority(raw)
        realized = (parse_rest_decimal_value_object(raw.get("equity"))
                    - parse_rest_decimal_value_object(raw.get("unrealized_profit")))
        if realized <= 0 or funds.available_cash < 0:
            raise V20FinamBlocked("BROKER_MONEY_NOT_VALID")
        return LiveAccountSnapshot(
            self.robot_id, self.account_hash, now.astimezone(timezone.utc),
            realized, funds.available_cash, positions, tuple(orders),
        )

    def authority(
        self, snapshot: LiveAccountSnapshot, *, symbol: str, direction: str,
        roundtrip_cost_per_contract: Decimal, now: datetime,
    ) -> AccountAuthority:
        """Refresh directional FINAM GO and use H1 R15/grid/lot semantics.

        Cost is an explicit broker-tariff input, never offline C1 or invented
        zero. The caller retains the responsibility to prove its source.
        """
        self._require_bound()
        if (symbol not in N4 or direction not in {"LONG", "SHORT"}
                or not isinstance(snapshot, LiveAccountSnapshot)
                or snapshot.robot_id != self.robot_id or snapshot.account_hash != self.account_hash
                or not isinstance(now, datetime) or now.tzinfo is None
                or now.utcoffset() is None):
            raise V20FinamBlocked("ACCOUNT_AUTHORITY_SCOPE_INVALID")
        elapsed = now.astimezone(timezone.utc) - snapshot.observed_at
        if not timedelta(0) <= elapsed <= timedelta(seconds=60):
            raise V20FinamBlocked("STALE_FINAM_ACCOUNT_SNAPSHOT")
        try:
            cost = Decimal(str(roundtrip_cost_per_contract))
        except (ValueError, TypeError, ArithmeticError) as exc:
            raise V20FinamBlocked("BROKER_TARIFF_INVALID") from exc
        if not cost.is_finite() or cost <= 0:
            raise V20FinamBlocked("BROKER_TARIFF_REQUIRED")
        registry = _load_registry()[symbol]
        params = self.api.asset_params(registry["finam_symbol"], self.account_id)
        go = directional_initial_margin(params, direction)
        return AccountAuthority(
            account_id=self.account_id,
            realized_equity=snapshot.realized_equity,
            available_cash=snapshot.available_cash,
            price_step=Decimal(registry["price_step"]),
            tick_value=Decimal(registry["tick_value"]),
            initial_margin=go,
            trade_lot_size=int(registry["quantity_granularity"]),
            roundtrip_cost_per_contract=cost,
        )
