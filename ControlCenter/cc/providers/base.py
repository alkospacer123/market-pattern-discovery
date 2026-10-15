"""Future adapters implement this bounded snapshot interface, never commands.

CC-01 intentionally includes no file, database, network or broker adapter.
"""
from datetime import datetime
from typing import Protocol
from ..models import RobotId, RobotSnapshot


class SnapshotProvider(Protocol):
    def snapshot(self, robot_id: RobotId, scenario: str, now: datetime) -> RobotSnapshot: ...
