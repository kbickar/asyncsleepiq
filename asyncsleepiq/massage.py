"""Massage state and control from the SleepIQ API."""
from __future__ import annotations

from typing import Any

from .api import SleepIQAPI
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
    """Massage state and control for one side of a bed."""

    max_massage_time = 60

    def __init__(self, api: SleepIQAPI, bed_id: str, side: Side) -> None:
        """Initialize the massage state."""
        self._api = api
        self.bed_id = bed_id
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

    async def set_speed(
        self,
        foot_speed: Speed | None = None,
        head_speed: Speed | None = None,
        timer: int | None = None,
    ) -> None:
        """Set the foot and head motor speeds through the API.

        A speed left as None keeps its current value. Without a timer, a
        running motor gets the current timer or the 60 minute maximum, since
        the bed clears an unused timer and nothing else would stop the motor.
        """
        foot = self.foot_speed if foot_speed is None else foot_speed
        head = self.head_speed if head_speed is None else head_speed
        running = foot != Speed.OFF or head != Speed.OFF
        if timer is None:
            timer = (self.timer or self.max_massage_time) if running else 0
        self._check_timer(timer)

        await self._adjust(
            {"footMassageMotor": foot, "headMassageMotor": head, "massageTimer": timer}
        )
        self.foot_speed = foot
        self.head_speed = head
        self.timer = timer
        if running:
            self.mode = Mode.OFF
        self.is_on = running or self.mode != Mode.OFF

    async def set_timer(self, timer: int) -> None:
        """Set the minutes left on this side's massage through the API."""
        self._check_timer(timer)
        await self._adjust({"massageTimer": timer})
        self.timer = timer

    async def turn_off(self) -> None:
        """Stop both motors through the API."""
        await self.set_speed(Speed.OFF, Speed.OFF, 0)

    async def set_massage(
        self, foot_speed: Speed, head_speed: Speed, timer: int = 0, mode: Mode = Mode.OFF
    ) -> None:
        """Send speeds, timer and mode in one request.

        This is the request SleepIQFoundation.set_foundation_massage has always
        sent. A mode other than OFF turns both speeds off.
        """
        if mode != Mode.OFF:
            foot_speed = Speed.OFF
            head_speed = Speed.OFF

        await self._adjust(
            {
                "footMassageMotor": foot_speed,
                "headMassageMotor": head_speed,
                "massageTimer": timer,
                "massageWaveMode": mode,
            }
        )
        self.foot_speed = foot_speed
        self.head_speed = head_speed
        self.timer = timer
        self.mode = mode
        self.is_on = mode != Mode.OFF or foot_speed != Speed.OFF or head_speed != Speed.OFF

    async def _adjust(self, data: dict[str, Any]) -> None:
        """Send a partial adjustment for this side, as the SleepIQ app does."""
        await self._api.put(
            f"bed/{self.bed_id}/foundation/adjustment", {**data, "side": self.side.value}
        )

    def _check_timer(self, timer: int) -> None:
        if type(timer) is not int or timer < 0 or timer > self.max_massage_time:
            raise ValueError(f"Invalid Time, must be between 0 and {self.max_massage_time}")
