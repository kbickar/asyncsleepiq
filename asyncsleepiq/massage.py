"""Massage state from the SleepIQ API."""
from __future__ import annotations

from typing import Any

from .consts import SIDES_FULL, Mode, Side, Speed

def _speed(value: Any) -> Speed:
    try:
        return Speed(value)
    except ValueError:
        return Speed.OFF


def _mode(value: Any) -> Mode:
    try:
        return Mode(value)
    except ValueError:
        return Mode.OFF


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

    def __str__(self) -> str:
        """Return the current massage state for debugging."""
        return (f"SleepIQMassage[{SIDES_FULL[self.side]}]: "
                f"{'On' if self.is_on else 'Off'}, foot={self.foot_speed.name}, "
                f"head={self.head_speed.name}, mode={self.mode.name}, timer={self.timer}")

    __repr__ = __str__

    async def update(self, data: dict[str, Any]) -> None:
        """Read this side's state and remaining minutes from the bed response."""
        side_data = data.get(f"{SIDES_FULL[self.side].lower()}Side")
        if not isinstance(side_data, dict):
            return

        self.is_on = side_data.get("massageMotorStatus") == 1
        self.foot_speed = _speed(side_data.get("footMassageMotorSpeed"))
        self.head_speed = _speed(side_data.get("headMassageMotorSpeed"))
        self.mode = _mode(side_data.get("waveMode"))
        timer = side_data.get("massageTimer")
        self.timer = timer if type(timer) is int and timer >= 0 else 0
