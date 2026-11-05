"""Massage state from the SleepIQ API."""
from __future__ import annotations

from typing import Any, TypeVar

from .consts import SIDES_FULL, Mode, Side, Speed

_MassageEnum = TypeVar("_MassageEnum", Mode, Speed)


def _enum_or_off(value: Any, off: _MassageEnum) -> _MassageEnum:
    try:
        return type(off)(value)
    except ValueError:
        return off


class SleepIQMassage:
    """Massage state for one side of a bed."""

    def __init__(self, side: Side) -> None:
        """Initialize the massage state."""
        self.side = side
        self.is_on = False
        self.foot_speed = Speed.OFF
        self.head_speed = Speed.OFF
        self.mode = Mode.OFF
        self.timer = 0

    async def update(self, data: dict[str, Any]) -> None:
        """Read this side's state and remaining minutes from the bed response."""
        side_data = data.get(f"{SIDES_FULL[self.side].lower()}Side")
        if not isinstance(side_data, dict):
            return

        self.is_on = side_data.get("massageMotorStatus") == 1
        self.foot_speed = _enum_or_off(side_data.get("footMassageMotorSpeed"), Speed.OFF)
        self.head_speed = _enum_or_off(side_data.get("headMassageMotorSpeed"), Speed.OFF)
        self.mode = _enum_or_off(side_data.get("waveMode"), Mode.OFF)
        timer = side_data.get("massageTimer")
        self.timer = timer if type(timer) is int and timer >= 0 else 0
