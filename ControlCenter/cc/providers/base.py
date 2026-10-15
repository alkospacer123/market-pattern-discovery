"""Future adapters implement this bounded snapshot interface, never commands.

CC-02 adds only the bounded packaged H1 offline JSON receiver. No commands,
database, network or broker capability.
"""
from datetime import datetime
from typing import Protocol
from ..models import RobotId, RobotSnapshot


class SnapshotProvider(Protocol):
    def snapshot(self, robot_id: RobotId, scenario: str, now: datetime) -> RobotSnapshot: ...
